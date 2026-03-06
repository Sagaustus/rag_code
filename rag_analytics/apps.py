from django.apps import AppConfig


class RagAnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rag_analytics"

    def ready(self) -> None:
        import rag_analytics.signals  # noqa: F401 — registers signal handlers
