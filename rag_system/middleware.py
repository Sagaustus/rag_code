from __future__ import annotations

import os
import secrets
from typing import Optional

from django.conf import settings
from django.http import JsonResponse


class ApiKeyMiddleware:
    """Require an API key for all /api/* routes.

    Accepts either:
      - Authorization: Bearer <token>
      - X-API-Key: <token>

    If settings.DEBUG is True and no RAG_API_KEY is set, requests are allowed
    to avoid blocking local development.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _extract_token(request) -> Optional[str]:
        auth = (request.headers.get("Authorization") or "").strip()
        if auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip() or None

        api_key = (request.headers.get("X-API-Key") or "").strip()
        return api_key or None

    def __call__(self, request):
        path = request.path or ""
        if not path.startswith("/api/"):
            return self.get_response(request)

        # Allow CORS preflight through.
        if request.method.upper() == "OPTIONS":
            return self.get_response(request)

        expected = (getattr(settings, "RAG_API_KEY", "") or os.getenv("RAG_API_KEY") or "").strip()
        if not expected and getattr(settings, "DEBUG", False):
            return self.get_response(request)

        provided = self._extract_token(request)
        if not provided or not secrets.compare_digest(provided, expected):
            return JsonResponse({"error": "Unauthorized"}, status=401)

        return self.get_response(request)
