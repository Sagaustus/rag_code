from __future__ import annotations

from typing import Any, Dict, List, Optional

import uuid

from django.conf import settings
from django.core import signing
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView

from rag_core.client import RagClientError, get_default_client
from rag_collections.models import CollectionMetadata

from .models import Conversation, Message

# Maximum number of prior messages sent as history to the LLM.
_HISTORY_LIMIT = 20

_SYSTEM_PROMPT = (
    "You are ImmiBot, the AI assistant powering imrag.ca — a Retrieval-Augmented "
    "Generation system specialized in Canadian immigration. You have access to a "
    "curated collection of over 800,000 Canadian immigration resources including "
    "IRCC official policies, Express Entry criteria, Provincial Nominee Programs "
    "(PNPs), work permits, study permits, family sponsorship, refugee & asylum "
    "claims, citizenship applications, NOC/TEER codes, LMIA requirements, and "
    "settlement services.\n\n"
    "RULES:\n"
    "1. Answer ONLY based on the retrieved documents. If the retrieved context "
    "does not contain enough information, say so clearly — never fabricate.\n"
    "2. Always cite the specific program, policy, or regulation you reference "
    "(e.g. 'Under Express Entry CRS criteria…', 'Per IRPA s.25…').\n"
    "3. Note that immigration rules change frequently. Recommend the user verify "
    "on the official IRCC website (canada.ca/immigration) for the latest.\n"
    "4. You provide INFORMATION only, NOT legal advice. Suggest consulting a "
    "licensed immigration consultant (RCIC) or lawyer for personal cases.\n"
    "5. If a question is unrelated to Canadian immigration, politely redirect: "
    "'I specialize in Canadian immigration. How can I help with that topic?'\n"
    "6. Be concise, clear, and well-structured. Use bullet points or numbered "
    "lists when comparing programs or listing requirements.\n"
    "7. When relevant, mention processing times, fees, and eligibility criteria."
)


_UID_COOKIE_NAME = "rag_uid"
_UID_SIGN_SALT = "rag_chat.uid"


def _get_or_create_ui_user_id(request: HttpRequest) -> tuple[str, bool]:
    """Return (external_user_id, was_created).

    Uses a signed cookie so the browser never needs to send secrets and users
    can't easily impersonate other users by guessing an id.
    """

    raw = (request.COOKIES.get(_UID_COOKIE_NAME) or "").strip()
    if raw:
        try:
            value = signing.Signer(salt=_UID_SIGN_SALT).unsign(raw)
            if value:
                return value, False
        except Exception:
            pass

    return uuid.uuid4().hex, True


def _sign_ui_user_id(external_user_id: str) -> str:
    return signing.Signer(salt=_UID_SIGN_SALT).sign(external_user_id)


def _resolve_collection(data: dict) -> tuple[Optional[CollectionMetadata], str]:
    """Return (CollectionMetadata or None, raw_collection_id_string)."""
    coll_key = (data.get("collection_key") or "").strip()
    raw = (
        (data.get("collection") or "")
        or (data.get("collection_id") or "")
        or (data.get("index_id") or "")
    ).strip()
    collection: Optional[CollectionMetadata] = None
    if coll_key:
        collection = CollectionMetadata.objects.filter(key=coll_key).first()
    if collection is None and raw:
        collection = CollectionMetadata.objects.filter(ionos_collection_id=raw).first()
    return collection, raw


def _build_chat_messages(conversation: Conversation, current_query: str) -> List[Dict[str, Any]]:
    """Build an OpenAI-format messages list from DB history + the current query.

    Fetches the last ``_HISTORY_LIMIT`` user/assistant turns from the
    conversation so the LLM has multi-turn context.
    """
    prior = list(
        Message.objects.filter(
            conversation=conversation,
            role__in=[Message.ROLE_USER, Message.ROLE_ASSISTANT],
        )
        .order_by("-created_at", "-id")[:_HISTORY_LIMIT]
    )
    prior.reverse()
    messages: List[Dict[str, Any]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend({"role": m.role, "content": m.content} for m in prior)
    messages.append({"role": "user", "content": current_query})
    return messages


def _execute_logged_chat(
    conversation: Conversation,
    query: str,
    collection: Optional[CollectionMetadata],
    raw_collection: str,
) -> tuple[str, List[Dict[str, Any]]]:
    """Persist the user message, call RagClient with full history, persist the reply.

    Returns (answer_text, sources) on success.
    Raises RagClientError on backend failure (after logging a system message).
    """
    messages = _build_chat_messages(conversation, query)

    Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_USER,
        content=query,
        collection=collection,
    )

    index_override = collection.ionos_collection_id if collection else raw_collection or None
    try:
        rag_resp = get_default_client().chat(messages=messages, index_id=index_override)
        answer_text = rag_resp.text
        sources: List[Dict[str, Any]] = rag_resp.sources
    except RagClientError as exc:
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_SYSTEM,
            content=f"RAG backend error: {exc}",
            collection=collection,
        )
        raise

    Message.objects.create(
        conversation=conversation,
        role=Message.ROLE_ASSISTANT,
        content=answer_text,
        collection=collection,
        sources=sources or None,
    )
    return answer_text, sources


class ChatPageView(View):
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        external_user_id, created = _get_or_create_ui_user_id(request)
        resp = render(request, "rag_chat/chat.html")
        if created:
            resp.set_cookie(
                _UID_COOKIE_NAME,
                _sign_ui_user_id(external_user_id),
                httponly=True,
                samesite="Lax",
                secure=not settings.DEBUG,
            )
        return resp


class ChatProxyView(APIView):
    """POST /chat/send/ – server-side proxy for the Chat UI.

    Authenticated via signed cookie; does not require an API key.
    """

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        external_user_id, _ = _get_or_create_ui_user_id(request)
        data = request.data or {}
        query = (data.get("query") or "").strip()
        if not query:
            return Response({"error": "Missing query"}, status=400)
        if len(query) > settings.RAG_MAX_QUERY_LENGTH:
            return Response({"error": f"Query exceeds {settings.RAG_MAX_QUERY_LENGTH} character limit"}, status=400)

        conv_id = data.get("conversation_id")
        conversation: Optional[Conversation] = None
        if conv_id:
            try:
                conversation = Conversation.objects.filter(pk=int(conv_id), external_user_id=external_user_id).first()
            except Exception:
                conversation = None
        if conversation is None:
            conversation = Conversation.objects.create(
                external_user_id=external_user_id,
                title=(query[:80] or "Conversation"),
            )

        collection, raw_collection = _resolve_collection(data)
        try:
            answer_text, sources = _execute_logged_chat(conversation, query, collection, raw_collection)
        except RagClientError as exc:
            return Response({"error": str(exc)}, status=502)

        return Response(
            {
                "conversation_id": conversation.id,
                "answer": answer_text,
                "sources": sources,
                "collection": getattr(collection, "key", None),
                "collection_id": getattr(collection, "ionos_collection_id", raw_collection or None),
                "error": None,
            }
        )


class ConversationsView(APIView):
    """GET /api/chat/conversations/?external_user_id=... – list recent threads.

    Intended for the built-in UI. If external_user_id is omitted, returns an empty list.
    """

    def get(self, request, *args, **kwargs):  # type: ignore[override]
        external_user_id = (request.query_params.get("external_user_id") or "").strip()
        if not external_user_id:
            return Response({"conversations": []})

        conversations = (
            Conversation.objects.filter(external_user_id=external_user_id)
            .order_by("-created_at", "-id")
            .values("id", "title", "created_at")[:50]
        )
        return Response({"conversations": list(conversations)})


class ConversationMessagesView(APIView):
    """GET /api/chat/session/<id>/messages/?external_user_id=... – fetch messages.

    external_user_id is required and must match the conversation's owner.
    """

    def get(self, request, conversation_id: int, *args, **kwargs):  # type: ignore[override]
        external_user_id = (request.query_params.get("external_user_id") or "").strip()
        if not external_user_id:
            return Response({"error": "external_user_id is required"}, status=400)

        conversation = Conversation.objects.filter(pk=conversation_id, external_user_id=external_user_id).first()
        if conversation is None:
            return Response({"error": "Conversation not found"}, status=404)

        messages = (
            Message.objects.filter(conversation_id=conversation_id)
            .order_by("created_at", "id")
            .values("id", "role", "content", "sources", "created_at")
        )
        return Response(
            {
                "conversation_id": conversation.id,
                "title": conversation.title,
                "messages": list(messages),
            }
        )


class UIConversationsView(APIView):
    """GET /chat/conversations/ – list threads for the current UI cookie user."""

    def get(self, request, *args, **kwargs):  # type: ignore[override]
        external_user_id, _ = _get_or_create_ui_user_id(request)
        conversations = (
            Conversation.objects.filter(external_user_id=external_user_id)
            .order_by("-created_at", "-id")
            .values("id", "title", "created_at")[:50]
        )
        return Response({"conversations": list(conversations)})


class UIConversationMessagesView(APIView):
    """GET /chat/session/<id>/messages/ – messages for the current UI cookie user."""

    def get(self, request, conversation_id: int, *args, **kwargs):  # type: ignore[override]
        external_user_id, _ = _get_or_create_ui_user_id(request)
        conversation = Conversation.objects.filter(pk=conversation_id, external_user_id=external_user_id).first()
        if conversation is None:
            return Response({"error": "Conversation not found"}, status=404)

        messages = (
            Message.objects.filter(conversation_id=conversation_id)
            .order_by("created_at", "id")
            .values("id", "role", "content", "sources", "created_at")
        )
        return Response(
            {
                "conversation_id": conversation.id,
                "title": conversation.title,
                "messages": list(messages),
            }
        )


class LoggedChatView(APIView):
    """POST /api/chat/session/ – chat with logging & collections.

    Request JSON fields:
      - query (str, required)
      - conversation_id (int, optional): continue existing conversation
      - external_user_id (str, optional): for analytics / cross-app linkage
      - collection_key (str, optional): lookup CollectionMetadata.key
      - collection (str, optional): fallback raw IONOS collection/index UUID

    Response JSON (on success):
      {"conversation_id", "answer", "sources", "collection", "collection_id"}
    """

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        data = request.data or {}
        query = (data.get("query") or "").strip()
        if not query:
            return Response({"error": "Missing query"}, status=400)
        if len(query) > settings.RAG_MAX_QUERY_LENGTH:
            return Response({"error": f"Query exceeds {settings.RAG_MAX_QUERY_LENGTH} character limit"}, status=400)

        external_user_id = (data.get("external_user_id") or "").strip()
        conv_id = data.get("conversation_id")

        conversation: Optional[Conversation] = None
        if conv_id:
            try:
                qs = Conversation.objects.filter(pk=int(conv_id))
                if external_user_id:
                    qs = qs.filter(external_user_id=external_user_id)
                conversation = qs.first()
            except Exception:
                conversation = None
        if conversation is None:
            conversation = Conversation.objects.create(
                external_user_id=external_user_id,
                title=(query[:80] or "Conversation"),
            )

        collection, raw_collection = _resolve_collection(data)
        try:
            answer_text, sources = _execute_logged_chat(conversation, query, collection, raw_collection)
        except RagClientError as exc:
            return Response({"error": str(exc)}, status=502)

        return Response(
            {
                "conversation_id": conversation.id,
                "answer": answer_text,
                "sources": sources,
                "collection": getattr(collection, "key", None),
                "collection_id": getattr(collection, "ionos_collection_id", raw_collection or None),
                "error": None,
            }
        )
