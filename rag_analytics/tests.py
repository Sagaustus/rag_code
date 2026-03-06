from __future__ import annotations

from django.test import TestCase
from django.utils import timezone

from rag_analytics.models import DailyUsageSnapshot
from rag_chat.models import Conversation, Message


class DailySnapshotSignalTest(TestCase):
    def setUp(self):
        self.conv = Conversation.objects.create(title="test conv")

    def _today(self):
        return timezone.now().date()

    def _snapshot(self):
        return DailyUsageSnapshot.objects.filter(date=self._today()).first()

    # --- user messages

    def test_user_message_increments_total_queries(self):
        Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="q")
        snap = self._snapshot()
        self.assertIsNotNone(snap)
        self.assertEqual(snap.total_queries, 1)
        self.assertEqual(snap.error_count, 0)

    def test_multiple_user_messages_accumulate(self):
        for _ in range(3):
            Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="q")
        self.assertEqual(self._snapshot().total_queries, 3)

    # --- assistant messages (should not affect counters)

    def test_assistant_message_creates_no_snapshot(self):
        Message.objects.create(conversation=self.conv, role=Message.ROLE_ASSISTANT, content="a")
        self.assertIsNone(self._snapshot())

    # --- system error messages

    def test_system_error_increments_error_count(self):
        Message.objects.create(
            conversation=self.conv,
            role=Message.ROLE_SYSTEM,
            content="RAG backend error: connection refused",
        )
        snap = self._snapshot()
        self.assertIsNotNone(snap)
        self.assertEqual(snap.error_count, 1)
        self.assertEqual(snap.total_queries, 0)

    def test_system_non_error_message_creates_no_snapshot(self):
        Message.objects.create(
            conversation=self.conv, role=Message.ROLE_SYSTEM, content="some info"
        )
        self.assertIsNone(self._snapshot())

    # --- update signal (created=False) must not re-increment

    def test_updating_message_does_not_double_count(self):
        msg = Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="q")
        msg.content = "updated"
        msg.save()
        self.assertEqual(self._snapshot().total_queries, 1)

    # --- mixed messages

    def test_query_and_error_both_counted(self):
        Message.objects.create(conversation=self.conv, role=Message.ROLE_USER, content="q")
        Message.objects.create(
            conversation=self.conv,
            role=Message.ROLE_SYSTEM,
            content="RAG backend error: timeout",
        )
        snap = self._snapshot()
        self.assertEqual(snap.total_queries, 1)
        self.assertEqual(snap.error_count, 1)
