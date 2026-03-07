from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.core import signing
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from rag_core.client import RagClientError, RagResponse
from rag_chat.models import Conversation, Message
from rag_chat.views import _build_chat_messages, _resolve_collection, _SYSTEM_PROMPT
from rag_collections.models import CollectionMetadata

_VALID_KEY = "test-api-key"
_NO_THROTTLE = {"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}
_UID_COOKIE = "rag_uid"
_UID_SALT = "rag_chat.uid"


def _signed_cookie(user_id: str) -> str:
    return signing.Signer(salt=_UID_SALT).sign(user_id)


def _mock_rag_client(answer: str = "answer") -> MagicMock:
    mock = MagicMock()
    mock.chat.return_value = RagResponse(data={"choices": [{"message": {"content": answer}}]})
    return mock


# ---------------------------------------------------------------------------
# _build_chat_messages helper
# ---------------------------------------------------------------------------

class BuildChatMessagesTest(TestCase):
    def setUp(self):
        self.conv = Conversation.objects.create(title="test")

    def test_empty_history_returns_system_plus_user_message(self):
        msgs = _build_chat_messages(self.conv, "hello")
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0], {"role": "system", "content": _SYSTEM_PROMPT})
        self.assertEqual(msgs[1], {"role": "user", "content": "hello"})

    def test_prior_user_and_assistant_messages_included(self):
        Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="q1")
        Message.objects.create(conversation=self.conv, role=Message.ROLE_ASSISTANT, content="a1")
        msgs = _build_chat_messages(self.conv, "q2")
        # system + 2 history + current = 4
        self.assertEqual(len(msgs), 4)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[1], {"role": "user", "content": "q1"})
        self.assertEqual(msgs[2], {"role": "assistant", "content": "a1"})
        self.assertEqual(msgs[3], {"role": "user", "content": "q2"})

    def test_db_system_messages_excluded_from_history(self):
        Message.objects.create(conversation=self.conv, role=Message.ROLE_SYSTEM, content="err")
        Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="q1")
        msgs = _build_chat_messages(self.conv, "q2")
        # Only the injected system prompt should be present, not DB system messages
        roles = [m["role"] for m in msgs]
        self.assertEqual(roles.count("system"), 1)
        self.assertEqual(msgs[0]["content"], _SYSTEM_PROMPT)

    def test_history_capped_at_limit(self):
        from rag_chat import views as cv
        # Create more messages than the cap
        for i in range(cv._HISTORY_LIMIT + 5):
            Message.objects.create(
                conversation=self.conv, role=Message.ROLE_USER, content=f"q{i}"
            )
        msgs = _build_chat_messages(self.conv, "current")
        # system + cap + current query
        self.assertEqual(len(msgs), cv._HISTORY_LIMIT + 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[-1], {"role": "user", "content": "current"})


# ---------------------------------------------------------------------------
# _resolve_collection helper
# ---------------------------------------------------------------------------

class ResolveCollectionTest(TestCase):
    def setUp(self):
        self.coll = CollectionMetadata.objects.create(
            key="test-coll", name="Test", ionos_collection_id="uuid-123"
        )

    def test_resolves_by_collection_key(self):
        coll, raw = _resolve_collection({"collection_key": "test-coll"})
        self.assertEqual(coll, self.coll)

    def test_resolves_by_ionos_id(self):
        coll, raw = _resolve_collection({"collection": "uuid-123"})
        self.assertEqual(coll, self.coll)
        self.assertEqual(raw, "uuid-123")

    def test_unknown_key_returns_none_collection(self):
        coll, _ = _resolve_collection({"collection_key": "nonexistent"})
        self.assertIsNone(coll)

    def test_empty_data_returns_none_and_empty_raw(self):
        coll, raw = _resolve_collection({})
        self.assertIsNone(coll)
        self.assertEqual(raw, "")


# ---------------------------------------------------------------------------
# ChatProxyView  (/chat/send/)
# ---------------------------------------------------------------------------

@override_settings(RAG_API_KEY=_VALID_KEY, RAG_MAX_QUERY_LENGTH=2000, REST_FRAMEWORK=_NO_THROTTLE)
class ChatProxyViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/chat/send/"
        self.user_id = "user-abc"
        self.client.cookies[_UID_COOKIE] = _signed_cookie(self.user_id)

    def _post(self, data):
        return self.client.post(self.url, data, format="json")

    def test_missing_query_returns_400(self):
        resp = self._post({})
        self.assertEqual(resp.status_code, 400)

    @override_settings(RAG_MAX_QUERY_LENGTH=5)
    def test_query_too_long_returns_400(self):
        resp = self._post({"query": "x" * 6})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("character limit", resp.json()["error"])

    def test_creates_new_conversation_and_returns_answer(self):
        mock = _mock_rag_client("hello back")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({"query": "hello"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("conversation_id", data)
        self.assertEqual(data["answer"], "hello back")
        self.assertIsNone(data["error"])

    def test_continues_existing_own_conversation(self):
        conv = Conversation.objects.create(external_user_id=self.user_id, title="mine")
        mock = _mock_rag_client("continued")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({"query": "follow-up", "conversation_id": conv.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["conversation_id"], conv.id)

    def test_cannot_hijack_another_users_conversation(self):
        other_conv = Conversation.objects.create(external_user_id="other-user", title="theirs")
        mock = _mock_rag_client("new")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({"query": "hijack", "conversation_id": other_conv.id})
        self.assertEqual(resp.status_code, 200)
        # A new conversation is created; the victim's is untouched
        self.assertNotEqual(resp.json()["conversation_id"], other_conv.id)
        self.assertEqual(Message.objects.filter(conversation=other_conv).count(), 0)

    def test_user_and_assistant_messages_saved(self):
        mock = _mock_rag_client("response")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({"query": "my question"})
        conv_id = resp.json()["conversation_id"]
        roles = set(Message.objects.filter(conversation_id=conv_id).values_list("role", flat=True))
        self.assertIn(Message.ROLE_USER, roles)
        self.assertIn(Message.ROLE_ASSISTANT, roles)

    def test_history_passed_to_llm_on_followup(self):
        conv = Conversation.objects.create(external_user_id=self.user_id, title="mine")
        Message.objects.create(conversation=conv, role=Message.ROLE_USER, content="first q")
        Message.objects.create(conversation=conv, role=Message.ROLE_ASSISTANT, content="first a")
        mock = _mock_rag_client()
        with patch("rag_chat.views.get_default_client", return_value=mock):
            self._post({"query": "second q", "conversation_id": conv.id})
        messages_sent = mock.chat.call_args.kwargs.get("messages") or mock.chat.call_args.args[0]
        # system (1) + history (2) + current (1) = 4
        self.assertEqual(len(messages_sent), 4)
        self.assertEqual(messages_sent[0]["role"], "system")
        self.assertEqual(messages_sent[1]["content"], "first q")

    def test_backend_error_returns_502_and_saves_system_message(self):
        with patch("rag_chat.views.get_default_client") as mf:
            mf.return_value.chat.side_effect = RagClientError("timed out")
            resp = self._post({"query": "hello"})
        self.assertEqual(resp.status_code, 502)
        self.assertTrue(
            Message.objects.filter(
                role=Message.ROLE_SYSTEM, content__contains="timed out"
            ).exists()
        )


# ---------------------------------------------------------------------------
# LoggedChatView  (/api/chat/session/)
# ---------------------------------------------------------------------------

@override_settings(RAG_API_KEY=_VALID_KEY, RAG_MAX_QUERY_LENGTH=2000, REST_FRAMEWORK=_NO_THROTTLE)
class LoggedChatViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/chat/session/"
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {_VALID_KEY}"}

    def _post(self, data):
        return self.client.post(self.url, data, format="json", **self.auth)

    def test_creates_conversation_with_provided_user_id(self):
        mock = _mock_rag_client("hi")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({"query": "hello", "external_user_id": "user-1"})
        self.assertEqual(resp.status_code, 200)
        conv = Conversation.objects.get(pk=resp.json()["conversation_id"])
        self.assertEqual(conv.external_user_id, "user-1")

    def test_can_continue_own_conversation(self):
        conv = Conversation.objects.create(external_user_id="user-1", title="mine")
        mock = _mock_rag_client("continued")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({"query": "follow up", "external_user_id": "user-1", "conversation_id": conv.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["conversation_id"], conv.id)

    def test_cannot_inject_into_another_users_conversation(self):
        """Fix 2b: conversation lookup is scoped to external_user_id."""
        victim_conv = Conversation.objects.create(external_user_id="victim", title="theirs")
        mock = _mock_rag_client("new conv")
        with patch("rag_chat.views.get_default_client", return_value=mock):
            resp = self._post({
                "query": "attack",
                "external_user_id": "attacker",
                "conversation_id": victim_conv.id,
            })
        self.assertEqual(resp.status_code, 200)
        # A new conversation is created; victim's is untouched
        self.assertNotEqual(resp.json()["conversation_id"], victim_conv.id)
        self.assertEqual(Message.objects.filter(conversation=victim_conv).count(), 0)

    def test_no_api_key_returns_401(self):
        resp = self.client.post(self.url, {"query": "hello"}, format="json")
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# ConversationMessagesView  (/api/chat/session/<id>/messages/)
# ---------------------------------------------------------------------------

@override_settings(RAG_API_KEY=_VALID_KEY, REST_FRAMEWORK=_NO_THROTTLE)
class ConversationMessagesViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {_VALID_KEY}"}
        self.user_id = "owner-user"
        self.conv = Conversation.objects.create(external_user_id=self.user_id, title="mine")
        Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="hi")

    def _url(self, conv_id):
        return f"/api/chat/session/{conv_id}/messages/"

    def test_missing_external_user_id_returns_400(self):
        """Fix 2a: external_user_id is now required."""
        resp = self.client.get(self._url(self.conv.id), **self.auth)
        self.assertEqual(resp.status_code, 400)

    def test_correct_owner_retrieves_messages(self):
        resp = self.client.get(
            self._url(self.conv.id), {"external_user_id": self.user_id}, **self.auth
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["messages"]), 1)
        self.assertEqual(resp.json()["messages"][0]["content"], "hi")

    def test_wrong_owner_gets_404(self):
        """Fix 2a: wrong external_user_id returns 404 (not the data)."""
        resp = self.client.get(
            self._url(self.conv.id), {"external_user_id": "impersonator"}, **self.auth
        )
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_conversation_returns_404(self):
        resp = self.client.get(
            self._url(99999), {"external_user_id": self.user_id}, **self.auth
        )
        self.assertEqual(resp.status_code, 404)
