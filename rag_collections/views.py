from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CollectionMetadata


class CollectionListView(APIView):
    """GET /chat/collections/ — public list of available collections for the UI."""

    def get(self, request, *args, **kwargs):
        collections = CollectionMetadata.objects.values(
            "key", "name", "description", "tags", "trust_score", "doc_count_snapshot",
        )
        return Response({"collections": list(collections)})
