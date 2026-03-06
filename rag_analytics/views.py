from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyUsageSnapshot


class DailyStatsView(APIView):
    """GET /api/analytics/daily/?days=30 – recent per-day usage totals."""

    def get(self, request, *args, **kwargs) -> Response:
        try:
            days = max(1, min(int(request.query_params.get("days", 30)), 365))
        except (ValueError, TypeError):
            days = 30

        snapshots = (
            DailyUsageSnapshot.objects.order_by("-date")
            .values("date", "total_queries", "error_count")[:days]
        )
        return Response({"stats": list(snapshots)})
