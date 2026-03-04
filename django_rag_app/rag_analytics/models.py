from __future__ import annotations

from django.db import models


# For now analytics will be computed from chat + collections tables; this app
# exists as a placeholder for future materialized views or summary tables.

class DailyUsageSnapshot(models.Model):
    """Optional aggregated usage stats per day (placeholder)."""

    date = models.DateField(unique=True)
    total_queries = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
