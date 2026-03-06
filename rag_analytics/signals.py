from __future__ import annotations

from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender="rag_chat.Message")
def update_daily_snapshot(sender, instance, created, **kwargs) -> None:
    """Increment DailyUsageSnapshot counters whenever a Message is created.

    - A ``user`` message = one query.
    - A ``system`` message containing the RAG error marker = one error.
    """
    if not created:
        return

    from rag_analytics.models import DailyUsageSnapshot  # local import avoids circular deps

    today = timezone.now().date()

    if instance.role == "user":
        snapshot, _ = DailyUsageSnapshot.objects.get_or_create(date=today)
        DailyUsageSnapshot.objects.filter(pk=snapshot.pk).update(total_queries=F("total_queries") + 1)
    elif instance.role == "system" and "RAG backend error" in (instance.content or ""):
        snapshot, _ = DailyUsageSnapshot.objects.get_or_create(date=today)
        DailyUsageSnapshot.objects.filter(pk=snapshot.pk).update(error_count=F("error_count") + 1)
