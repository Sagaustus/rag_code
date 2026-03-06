from __future__ import annotations

from django.db import models

from rag_collections.models import CollectionMetadata


class Conversation(models.Model):
    """A logical chat session, optionally tied to an external user ID."""

    external_user_id = models.CharField(max_length=128, blank=True, help_text="BridgeQuest user id or email hash, if available.")
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title or f"Conversation {self.pk}"


class Message(models.Model):
    """A single message in a conversation (user / assistant / system)."""

    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
        (ROLE_SYSTEM, "System"),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()

    collection = models.ForeignKey(
        CollectionMetadata,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Collection that backed this answer, if any.",
    )
    sources = models.JSONField(blank=True, null=True, help_text="Normalized list of source documents used for this answer.")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
