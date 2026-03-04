from __future__ import annotations

from django.db import models


class CollectionMetadata(models.Model):
    """Local metadata for an external IONOS document collection.

    This lets us annotate raw IONOS collections with human-friendly labels,
    tags, and transparency information without duplicating documents.
    """

    key = models.SlugField(max_length=64, unique=True, help_text="Stable key used by UIs, e.g. 'canadian-immigration'.")
    name = models.CharField(max_length=200, help_text="Human-readable name for this collection.")
    ionos_collection_id = models.CharField(max_length=128, unique=True, help_text="IONOS collection/ index UUID.")

    description = models.TextField(blank=True)
    tags = models.JSONField(blank=True, null=True, help_text="Optional list/dict of topical tags.")

    trust_score = models.FloatField(default=0.0, help_text="0–1 score expressing overall source reliability.")
    last_ingest_at = models.DateTimeField(blank=True, null=True)
    doc_count_snapshot = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.key})"
