from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from rag_core.client import RagClient, RagClientError, RagResponse
from rag_system.middleware import ApiKeyMiddleware

_VALID_KEY = "test-api-key"
_NO_THROTTLE = {"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}


def _mock_rag_client(answer: str = "test answer") -> MagicMock:
    mock = MagicMock()
    mock.chat.return_value = RagResponse(data={"choices": [{"message": {"content": answer}}]})
    mock.index_id = ""
    return mock


# ---------------------------------------------------------------------------
# RagResponse parsing
# ---------------------------------------------------------------------------

class RagResponseParseTest(TestCase):
    def test_text_openai_style(self):
        r = RagResponse(data={"choices": [{"message": {"content": "hello"}}]})
        self.assertEqual(r.text, "hello")

    def test_text_fallback_field(self):
        self.assertEqual(RagResponse(data={"text": "hi"}).text, "hi")

    def test_text_empty_data(self):
        self.assertEqual(RagResponse(data={}).text, "")

    def test_sources_from_sources_key(self):
        r = RagResponse(data={"sources": [{"title": "doc"}]})
        self.assertEqual(r.sources, [{"title": "doc"}])

    def test_sources_from_documents_key(self):
        r = RagResponse(data={"documents": [{"id": 1}]})
        self.assertEqual(r.sources, [{"id": 1}])

    def test_sources_filters_non_dicts(self):
        r = RagResponse(data={"sources": [{"ok": True}, "bad", 0]})
        self.assertEqual(r.sources, [{"ok": True}])

    def test_sources_empty_data(self):
        self.assertEqual(RagResponse(data={}).sources, [])


# ---------------------------------------------------------------------------
# RagClient initialisation validation
# ---------------------------------------------------------------------------

_BLANK_ENV = {
    "IONOS_RAG_API_KEY": "",
    "IONOS_RAG_BASE_URL": "",
    "IONOS_RAG_CHAT_ENDPOINT": "",
    "IONOS_RAG_MODEL_ID": "",
    "IONOS_RAG_INDEX_ID": "",
}


class RagClientInitTest(TestCase):
    @patch.dict("os.environ", _BLANK_ENV)
    def test_raises_on_missing_api_key(self):
        with self.assertRaises(RagClientError):
            RagClient(base_url="http://x.com", model_id="m", api_key="")

    @patch.dict("os.environ", _BLANK_ENV)
    def test_raises_on_missing_base_url_and_endpoint(self):
        with self.assertRaises(RagClientError):
            RagClient(api_key="key", model_id="m")

    @patch.dict("os.environ", _BLANK_ENV)
    def test_raises_on_missing_model_id(self):
        with self.assertRaises(RagClientError):
            RagClient(api_key="key", base_url="http://x.com", model_id="")

    def test_valid_init_with_chat_endpoint(self):
        c = RagClient(
            api_key="key",
            chat_endpoint="http://x.com/v1/chat/completions",
            model_id="m",
        )
        self.assertEqual(c.model_id, "m")


# ---------------------------------------------------------------------------
# ApiKeyMiddleware
# ---------------------------------------------------------------------------

@override_settings(RAG_API_KEY=_VALID_KEY, DEBUG=False)
class ApiKeyMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _run(self, request, sentinel=None):
        """Run middleware, returning either the sentinel (pass-through) or the response."""
        if sentinel is None:
            sentinel = object()

        def get_response(_req):
            return sentinel

        return ApiKeyMiddleware(get_response)(request)

    def test_non_api_path_passes_through(self):
        sentinel = object()
        req = self.factory.get("/chat/")
        self.assertIs(self._run(req, sentinel), sentinel)

    def test_api_path_without_key_returns_401(self):
        from django.http import JsonResponse
        req = self.factory.post("/api/chat/", content_type="application/json")
        result = self._run(req)
        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 401)

    def test_api_path_with_bearer_token_passes(self):
        sentinel = object()
        req = self.factory.post(
            "/api/chat/",
            HTTP_AUTHORIZATION=f"Bearer {_VALID_KEY}",
            content_type="application/json",
        )
        self.assertIs(self._run(req, sentinel), sentinel)

    def test_api_path_with_x_api_key_passes(self):
        sentinel = object()
        req = self.factory.post(
            "/api/chat/",
            HTTP_X_API_KEY=_VALID_KEY,
            content_type="application/json",
        )
        self.assertIs(self._run(req, sentinel), sentinel)

    def test_options_passes_through(self):
        sentinel = object()
        req = self.factory.options("/api/chat/")
        self.assertIs(self._run(req, sentinel), sentinel)

    def test_wrong_key_returns_401(self):
        from django.http import JsonResponse
        req = self.factory.post(
            "/api/chat/",
            HTTP_AUTHORIZATION="Bearer wrong-key",
            content_type="application/json",
        )
        result = self._run(req)
        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 401)

    @override_settings(RAG_API_KEY="", DEBUG=True)
    def test_debug_mode_with_no_key_passes_through(self):
        sentinel = object()
        req = self.factory.post("/api/chat/", content_type="application/json")
        self.assertIs(self._run(req, sentinel), sentinel)


# ---------------------------------------------------------------------------
# ChatView (stateless /api/chat/)
# ---------------------------------------------------------------------------

@override_settings(RAG_API_KEY=_VALID_KEY, RAG_MAX_QUERY_LENGTH=2000, REST_FRAMEWORK=_NO_THROTTLE)
class ChatViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/chat/"
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {_VALID_KEY}"}

    def test_missing_query_returns_400(self):
        resp = self.client.post(self.url, {}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"], "Missing query")

    @override_settings(RAG_MAX_QUERY_LENGTH=5)
    def test_query_too_long_returns_400(self):
        resp = self.client.post(self.url, {"query": "x" * 6}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("character limit", resp.json()["error"])

    def test_successful_chat_returns_answer(self):
        mock = _mock_rag_client("The answer is 42")
        with patch("rag_core.views.get_default_client", return_value=mock):
            resp = self.client.post(self.url, {"query": "what is it?"}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["answer"], "The answer is 42")
        self.assertIsNone(resp.json()["error"])

    def test_chat_passes_system_prompt_and_user_message(self):
        mock = _mock_rag_client()
        with patch("rag_core.views.get_default_client", return_value=mock):
            self.client.post(self.url, {"query": "hello"}, format="json", **self.auth)
        call_kwargs = mock.chat.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs.args[0]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("ImmiBot", messages[0]["content"])
        self.assertEqual(messages[1], {"role": "user", "content": "hello"})

    def test_backend_error_returns_502(self):
        with patch("rag_core.views.get_default_client") as mf:
            mf.return_value.chat.side_effect = RagClientError("down")
            resp = self.client.post(self.url, {"query": "hello"}, format="json", **self.auth)
        self.assertEqual(resp.status_code, 502)
        self.assertIn("down", resp.json()["error"])

    def test_no_api_key_returns_401(self):
        resp = self.client.post(self.url, {"query": "hello"}, format="json")
        self.assertEqual(resp.status_code, 401)
