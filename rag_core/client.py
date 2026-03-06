"""BridgeQuest RAG client wrapping IONOS AI Model Hub.

Minimal version: provides a single `chat` helper that forwards a messages
list to an OpenAI-compatible chat completion endpoint configured via
environment variables. Collection/index routing is handled by
`IONOS_RAG_INDEX_ID`.

Use `get_default_client()` to obtain the process-level singleton instead of
constructing `RagClient()` on every request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import os
import requests


@dataclass
class RagResponse:
    data: Dict[str, Any]

    @property
    def text(self) -> str:
        """Best-effort extraction of the main answer text.

        Supports OpenAI-style {choices: [{message: {content}}]} and a few
        simpler shapes used by provider-specific responses.
        """
        if "choices" in self.data and self.data["choices"]:
            first = self.data["choices"][0]
            if isinstance(first, dict):
                msg = first.get("message") or {}
                if isinstance(msg, dict):
                    return str(msg.get("content", ""))
                if "text" in first:
                    return str(first.get("text", ""))
        return str(self.data.get("text", ""))

    @property
    def sources(self) -> List[Dict[str, Any]]:
        """Return any attached source documents in a normalized list form.

        Different backends may place sources under ``sources``, ``documents``,
        or ``data.sources``. We normalise to a simple list of dicts.
        """
        candidates = []
        raw = self.data.get("sources")
        if raw:
            candidates = raw
        if not candidates and isinstance(self.data.get("data"), dict):
            raw = self.data["data"].get("sources")
            if raw:
                candidates = raw
        if not candidates and self.data.get("documents"):
            candidates = self.data.get("documents")

        if isinstance(candidates, list):
            return [c for c in candidates if isinstance(c, dict)]
        return []


class RagClientError(Exception):
    pass


class RagClient:
    """Very small HTTP client for BridgeQuest RAG.

    Reads configuration from environment so this project can run standalone
    without depending on the game settings module.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        index_id: Optional[str] = None,
        chat_endpoint: Optional[str] = None,
    ) -> None:
        env = os.environ
        self.base_url = (base_url or env.get("IONOS_RAG_BASE_URL", "")).rstrip("/")
        self.chat_endpoint = chat_endpoint or env.get("IONOS_RAG_CHAT_ENDPOINT", "")
        self.api_key = api_key or env.get("IONOS_RAG_API_KEY", "")
        self.model_id = model_id or env.get("IONOS_RAG_MODEL_ID", "")
        self.index_id = index_id or env.get("IONOS_RAG_INDEX_ID", "")

        if not self.api_key:
            raise RagClientError("Missing IONOS_RAG_API_KEY")
        if not (self.chat_endpoint or self.base_url):
            raise RagClientError("Missing IONOS_RAG_BASE_URL or IONOS_RAG_CHAT_ENDPOINT")
        if not self.model_id:
            raise RagClientError("Missing IONOS_RAG_MODEL_ID")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        index_id: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> RagResponse:
        """Send a chat request with a full messages list.

        ``messages`` should be in OpenAI format: a list of
        ``{"role": "user"|"assistant"|"system", "content": "..."}`` dicts.
        Pass the full conversation history to enable multi-turn responses.

        ``index_id`` can override the default collection on a per-call basis,
        enabling multi-collection usage from a single service.
        """
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
        }
        effective_index = (index_id or self.index_id or "").strip()
        if effective_index:
            payload["index_id"] = effective_index
        if extra_params:
            payload.update(extra_params)

        url_candidates: List[str] = []
        if self.chat_endpoint:
            url_candidates.append(self.chat_endpoint)
        if self.base_url:
            url_candidates.append(f"{self.base_url}/v1/chat/completions")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[str] = None
        for url in url_candidates:
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
            except requests.RequestException as exc:  # pragma: no cover - network
                last_error = f"network error to {url}: {exc}"
                continue

            if not resp.ok:
                last_error = f"{url} -> {resp.status_code}: {resp.text[:400]}"
                continue

            try:
                data = resp.json()
            except ValueError as exc:  # pragma: no cover
                last_error = f"invalid JSON from {url}: {exc}"
                continue

            return RagResponse(data=data)

        raise RagClientError(last_error or "All candidate chat endpoints failed")


_default_client: Optional[RagClient] = None


def get_default_client() -> RagClient:
    """Return the process-level RagClient singleton, creating it on first call.

    Raises RagClientError if required environment variables are missing.
    """
    global _default_client
    if _default_client is None:
        _default_client = RagClient()
    return _default_client
