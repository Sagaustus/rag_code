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

from rag_core.views import ChatView
from rag_chat.views import LoggedChatView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Simple stateless chat (no DB logging):
    path("api/chat/", ChatView.as_view(), name="api_chat"),
    # Logged, conversation-aware chat endpoint:
    path("api/chat/session/", LoggedChatView.as_view(), name="api_chat_session"),
]
