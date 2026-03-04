from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from rag_core.client import RagClient, RagClientError
from rag_collections.models import CollectionMetadata

from .models import Conversation, Message


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

        external_user_id = (data.get("external_user_id") or "").strip() or ""
        conv_id = data.get("conversation_id")

        conversation: Optional[Conversation] = None
        if conv_id:
            try:
                conversation = Conversation.objects.filter(pk=int(conv_id)).first()
            except Exception:
                conversation = None

        if conversation is None:
            conversation = Conversation.objects.create(
                external_user_id=external_user_id,
                title=(query[:80] or "Conversation"),
            )

        # Resolve collection: prefer logical key, then raw UUID.
        collection: Optional[CollectionMetadata] = None
        coll_key = (data.get("collection_key") or "").strip()
        raw_collection = (
            (data.get("collection") or "")
            or (data.get("collection_id") or "")
            or (data.get("index_id") or "")
        ).strip()

        if coll_key:
            collection = CollectionMetadata.objects.filter(key=coll_key).first()
        if collection is None and raw_collection:
            collection = CollectionMetadata.objects.filter(ionos_collection_id=raw_collection).first()

        # Persist user message.
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=query,
            collection=collection,
        )

        try:
            client = RagClient()
            index_override = collection.ionos_collection_id if collection else raw_collection or None
            rag_resp = client.chat(prompt=query, index_id=index_override)
            answer_text = rag_resp.text
            sources: List[Dict[str, Any]] = rag_resp.sources
        except RagClientError as exc:
            # Log system message so we still have a trace in the conversation.
            Message.objects.create(
                conversation=conversation,
                role=Message.ROLE_SYSTEM,
                content=f"RAG backend error: {exc}",
                collection=collection,
            )
            return Response({"error": str(exc)}, status=502)

        # Persist assistant answer.
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_ASSISTANT,
            content=answer_text,
            collection=collection,
            sources=sources or None,
        )

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
