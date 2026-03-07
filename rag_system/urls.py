"""
URL configuration for rag_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from rag_analytics.views import DailyStatsView
from rag_collections.views import CollectionListView
from rag_core.views import ChatView
from rag_chat.views import (
    ChatPageView,
    ChatProxyView,
    ConversationMessagesView,
    ConversationsView,
    LoggedChatView,
    UIConversationMessagesView,
    UIConversationsView,
)

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="chat_ui", permanent=False)),
    path("admin/", admin.site.urls),
    # ChatGPT-style web UI:
    path("chat/", ChatPageView.as_view(), name="chat_ui"),
    path("chat/send/", ChatProxyView.as_view(), name="chat_send"),
    path("chat/collections/", CollectionListView.as_view(), name="chat_collections"),
    path("chat/conversations/", UIConversationsView.as_view(), name="chat_conversations"),
    path(
        "chat/session/<int:conversation_id>/messages/",
        UIConversationMessagesView.as_view(),
        name="chat_session_messages",
    ),

    # Simple stateless chat (no DB logging):
    path("api/chat/", ChatView.as_view(), name="api_chat"),
    # Logged, conversation-aware chat endpoint:
    path("api/chat/session/", LoggedChatView.as_view(), name="api_chat_session"),

    # UI helper APIs:
    path("api/chat/conversations/", ConversationsView.as_view(), name="api_chat_conversations"),
    path(
        "api/chat/session/<int:conversation_id>/messages/",
        ConversationMessagesView.as_view(),
        name="api_chat_session_messages",
    ),

    # Analytics:
    path("api/analytics/daily/", DailyStatsView.as_view(), name="api_analytics_daily"),
]
