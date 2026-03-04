from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView

from .client import RagClient, RagClientError


class ChatView(APIView):
    """Simple POST /api/chat endpoint wrapping RagClient.

    Body: {"query": "...", "collection": "optional-index-or-key"}
    Response: {"answer": "...", "sources": [...], "error": null}
    """

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        query = (request.data.get("query") or "").strip()
        if not query:
            return Response({"error": "Missing query"}, status=400)

        # Optional collection override. For now this is treated as a raw
        # collection/index UUID; front-ends can map human labels → IDs.
        collection = (
            (request.data.get("collection") or "")
            or (request.data.get("collection_id") or "")
            or (request.data.get("index_id") or "")
        ).strip() or None

        try:
            client = RagClient()
            rag_resp = client.chat(prompt=query, index_id=collection)
            return Response(
                {
                    "answer": rag_resp.text,
                    "sources": rag_resp.sources,
                    "collection_id": collection or client.index_id,
                    "error": None,
                }
            )
        except RagClientError as exc:
            return Response({"error": str(exc)}, status=502)
