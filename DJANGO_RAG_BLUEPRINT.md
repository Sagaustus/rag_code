# 🏗️ Enterprise Django RAG System - Complete Blueprint

## 🎯 System Overview

A production-ready Django application with full control over your RAG system, featuring:
- ✅ Admin panel for non-technical users
- ✅ Multi-format document management (PDF, DOCX, TXT, Videos, URLs)
- ✅ Prompt engineering controls with rubrics
- ✅ REST API for integrations
- ✅ Real-time chat interface
- ✅ User management & permissions
- ✅ Analytics & monitoring
- ✅ Celery for background tasks
- ✅ IONOS integration

---

## 📁 Project Structure

```
django_rag/
├── config/                          # Main Django project
│   ├── settings/
│   │   ├── base.py                 # Base settings
│   │   ├── development.py          # Dev settings
│   │   └── production.py           # Production settings
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py                   # Celery configuration
│
├── knowledge_base/                  # Document Management App
│   ├── models.py                   # Document, Collection, Tag models
│   ├── admin.py                    # Admin interface
│   ├── views.py                    # Document upload/management views
│   ├── serializers.py              # API serializers
│   ├── tasks.py                    # Celery tasks (processing)
│   ├── processors/
│   │   ├── pdf_processor.py
│   │   ├── docx_processor.py
│   │   ├── video_processor.py
│   │   ├── url_scraper.py
│   │   └── ionos_uploader.py
│   └── utils.py
│
├── chatbot/                         # Chat Interface App
│   ├── models.py                   # Conversation, Message models
│   ├── views.py                    # Chat views
│   ├── consumers.py                # WebSocket consumers
│   ├── serializers.py
│   ├── rag_engine.py               # RAG logic
│   └── admin.py
│
├── prompt_engineering/              # Prompt Control App
│   ├── models.py                   # PromptTemplate, Rubric models
│   ├── admin.py                    # Prompt management admin
│   ├── views.py
│   ├── serializers.py
│   ├── validators.py               # Rubric validators
│   └── templates/
│       └── default_prompts.json
│
├── users/                           # User Management
│   ├── models.py                   # Custom user model
│   ├── views.py
│   ├── permissions.py
│   └── admin.py
│
├── api/                             # REST API
│   ├── v1/
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── serializers.py
│   └── permissions.py
│
├── frontend/                        # Frontend Templates
│   ├── templates/
│   │   ├── base.html
│   │   ├── chat.html
│   │   ├── dashboard.html
│   │   └── admin/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── views.py
│
├── analytics/                       # Analytics & Monitoring
│   ├── models.py                   # Usage metrics
│   ├── views.py
│   └── reports.py
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── scripts/
│   ├── deploy.sh
│   ├── backup.sh
│   └── migrate_data.sh
│
├── manage.py
├── .env.example
├── .gitignore
├── README.md
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    └── USER_GUIDE.md
```

---

## 🗄️ Database Models

### 1. Knowledge Base Models

```python
# knowledge_base/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Collection(models.Model):
    """Organize documents into collections"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ionos_collection_id = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class DocumentType(models.TextChoices):
    PDF = 'PDF', 'PDF Document'
    DOCX = 'DOCX', 'Word Document'
    TXT = 'TXT', 'Text File'
    URL = 'URL', 'Web URL'
    VIDEO = 'VIDEO', 'Video (YouTube, etc.)'
    AUDIO = 'AUDIO', 'Audio File'


class ProcessingStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class Document(models.Model):
    """Store document metadata and processing status"""
    title = models.CharField(max_length=300)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DocumentType.choices)

    # File storage
    file = models.FileField(upload_to='documents/%Y/%m/%d/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    # Content
    extracted_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)

    # Processing
    status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    ionos_document_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)

    # Metadata
    file_size = models.BigIntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, default='en')

    # Tags & Categories
    tags = models.ManyToManyField('Tag', blank=True)

    # Tracking
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['document_type']),
        ]

    def __str__(self):
        return self.title


class Tag(models.Model):
    """Categorize documents"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3498db')

    def __str__(self):
        return self.name
```

### 2. Chatbot Models

```python
# chatbot/models.py

class Conversation(models.Model):
    """Track user conversations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200, blank=True)
    collection = models.ForeignKey('knowledge_base.Collection', on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Metrics
    message_count = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.session_id[:8]}"


class Message(models.Model):
    """Store chat messages"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()

    # RAG context
    retrieved_documents = models.JSONField(default=list, blank=True)
    prompt_used = models.ForeignKey('prompt_engineering.PromptTemplate', on_delete=models.SET_NULL, null=True)

    # Metadata
    tokens_used = models.IntegerField(default=0)
    response_time = models.FloatField(null=True, blank=True)  # seconds

    created_at = models.DateTimeField(auto_now_add=True)

    # User feedback
    rating = models.IntegerField(null=True, blank=True, choices=[(1,'👎'), (5,'👍')])
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
```

### 3. Prompt Engineering Models

```python
# prompt_engineering/models.py

class PromptTemplate(models.Model):
    """Manage prompt templates with rubrics"""
    name = models.CharField(max_length=200)
    description = models.TextField()

    # Prompt components
    system_message = models.TextField(help_text="System message/context")
    user_template = models.TextField(help_text="User message template with {variables}")

    # Rubrics (evaluation criteria)
    rubrics = models.JSONField(default=dict, help_text="""
    Example: {
        "accuracy": {"weight": 0.4, "description": "Factually correct"},
        "relevance": {"weight": 0.3, "description": "Answers the question"},
        "clarity": {"weight": 0.2, "description": "Clear and understandable"},
        "conciseness": {"weight": 0.1, "description": "Brief and to the point"}
    }
    """)

    # LLM settings
    model = models.CharField(max_length=100, default="meta-llama/Llama-3.3-70B-Instruct")
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1500)

    # RAG settings
    num_sources = models.IntegerField(default=3)
    min_similarity = models.FloatField(default=0.5)

    # Metadata
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Analytics
    usage_count = models.IntegerField(default=0)
    avg_rating = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return self.name

    def render_prompt(self, **kwargs):
        """Render prompt with variables"""
        return self.user_template.format(**kwargs)


class PromptVersion(models.Model):
    """Track prompt template versions"""
    template = models.ForeignKey(PromptTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    system_message = models.TextField()
    user_template = models.TextField()
    rubrics = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['template', 'version_number']
```

---

## 🎨 Admin Interface Design

### Custom Admin for Non-Technical Users

```python
# knowledge_base/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Collection, Document, Tag

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_count', 'created_by', 'created_at', 'status_badge']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['ionos_collection_id', 'created_at', 'updated_at']

    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'

    def status_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        return format_html(
            '<span style="color: {};">●</span> {}',
            color,
            'Active' if obj.is_active else 'Inactive'
        )
    status_badge.short_description = 'Status'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'collection', 'status_badge', 'uploaded_at', 'actions_column']
    list_filter = ['status', 'document_type', 'collection', 'uploaded_at']
    search_fields = ['title', 'extracted_text']
    readonly_fields = ['uploaded_by', 'uploaded_at', 'processed_at', 'ionos_document_id', 'file_size', 'word_count']

    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'collection', 'document_type', 'tags')
        }),
        ('Upload', {
            'fields': ('file', 'url')
        }),
        ('Content', {
            'fields': ('extracted_text', 'summary'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': ('status', 'ionos_document_id', 'error_message')
        }),
        ('Metadata', {
            'fields': ('file_size', 'word_count', 'language', 'uploaded_by', 'uploaded_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'COMPLETED': 'green',
            'FAILED': 'red'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def actions_column(self, obj):
        if obj.status == 'FAILED':
            return format_html('<a class="button" href="#">Retry</a>')
        elif obj.status == 'COMPLETED':
            return format_html('<a class="button" href="#">View in IONOS</a>')
        return '-'
    actions_column.short_description = 'Actions'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_preview', 'document_count']

    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background: {}; border-radius: 3px;"></div>',
            obj.color
        )
    color_preview.short_description = 'Color'

    def document_count(self, obj):
        return obj.document_set.count()
    document_count.short_description = 'Documents'
```

---

## ⚙️ Core Features Implementation

### 1. Document Processing (Celery Tasks)

```python
# knowledge_base/tasks.py

from celery import shared_task
from .models import Document, ProcessingStatus
from .processors import PDFProcessor, URLScraper, VideoProcessor
from .processors.ionos_uploader import upload_to_ionos
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_document(document_id):
    """Process and upload document to IONOS"""
    try:
        document = Document.objects.get(id=document_id)
        document.status = ProcessingStatus.PROCESSING
        document.save()

        # Extract text based on document type
        if document.document_type == 'PDF':
            processor = PDFProcessor()
            text = processor.extract_text(document.file.path)
        elif document.document_type == 'URL':
            processor = URLScraper()
            text = processor.scrape(document.url)
        elif document.document_type == 'VIDEO':
            processor = VideoProcessor()
            text = processor.extract_transcript(document.url)
        else:
            text = document.file.read().decode('utf-8')

        document.extracted_text = text
        document.word_count = len(text.split())

        # Upload to IONOS
        ionos_id = upload_to_ionos(
            collection_id=document.collection.ionos_collection_id,
            title=document.title,
            content=text
        )

        document.ionos_document_id = ionos_id
        document.status = ProcessingStatus.COMPLETED
        document.processed_at = timezone.now()
        document.save()

        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        document.status = ProcessingStatus.FAILED
        document.error_message = str(e)
        document.save()
```

### 2. RAG Engine

```python
# chatbot/rag_engine.py

import requests
from django.conf import settings

class RAGEngine:
    def __init__(self):
        self.ionos_token = settings.IONOS_API_TOKEN
        self.collection_id = settings.IONOS_COLLECTION_ID

    def query(self, user_message, conversation_history=None, prompt_template=None):
        """Main RAG query function"""
        # 1. Retrieve relevant documents
        documents = self.retrieve_documents(user_message, num_results=prompt_template.num_sources)

        # 2. Build context
        context = self.build_context(documents)

        # 3. Generate response
        response = self.generate_response(
            user_message=user_message,
            context=context,
            conversation_history=conversation_history,
            prompt_template=prompt_template
        )

        return {
            'response': response,
            'sources': documents,
            'prompt_used': prompt_template.id
        }

    def retrieve_documents(self, query, num_results=3):
        """Query IONOS vector database"""
        endpoint = f"https://inference.de-txl.ionos.com/collections/{self.collection_id}/query"
        headers = {
            "Authorization": f"Bearer {self.ionos_token}",
            "Content-Type": "application/json"
        }
        body = {"query": query, "limit": num_results}

        response = requests.post(endpoint, json=body, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()['properties']['matches']
        return []

    def generate_response(self, user_message, context, conversation_history, prompt_template):
        """Generate LLM response"""
        # Build messages
        messages = [
            {"role": "system", "content": prompt_template.system_message},
        ]

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 3 exchanges
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add current query with context
        user_prompt = prompt_template.render_prompt(
            context=context,
            question=user_message
        )
        messages.append({"role": "user", "content": user_prompt})

        # Call IONOS LLM
        endpoint = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.ionos_token}",
            "Content-Type": "application/json"
        }
        body = {
            "model": prompt_template.model,
            "messages": messages,
            "temperature": prompt_template.temperature,
            "max_tokens": prompt_template.max_tokens
        }

        response = requests.post(endpoint, json=body, headers=headers, timeout=90)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        raise Exception(f"LLM API error: {response.status_code}")
```

---

## 🔌 REST API Endpoints

```python
# api/v1/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('collections', views.CollectionViewSet)
router.register('documents', views.DocumentViewSet)
router.register('conversations', views.ConversationViewSet)
router.register('prompts', views.PromptTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', views.ChatAPIView.as_view(), name='chat'),
    path('upload/', views.DocumentUploadView.as_view(), name='upload'),
]
```

---

## 🎨 Frontend (Modern UI)

Using Django templates + HTMX + Alpine.js for reactivity

```html
<!-- frontend/templates/chat.html -->

{% extends 'base.html' %}

{% block content %}
<div class="chat-container" x-data="chatApp()">
    <!-- Chat Header -->
    <div class="chat-header">
        <h2>AI Assistant</h2>
        <div class="status" x-show="isTyping">
            <span class="typing-indicator">●●●</span> AI is thinking...
        </div>
    </div>

    <!-- Messages -->
    <div class="messages" id="messages">
        <template x-for="message in messages" :key="message.id">
            <div :class="'message message-' + message.role">
                <div class="content" x-text="message.content"></div>
                <div class="timestamp" x-text="message.timestamp"></div>
                <div class="sources" x-show="message.sources">
                    <template x-for="source in message.sources">
                        <span class="source-badge" x-text="source.name"></span>
                    </template>
                </div>
            </div>
        </template>
    </div>

    <!-- Input -->
    <div class="chat-input">
        <textarea
            x-model="inputMessage"
            @keydown.enter.prevent="sendMessage()"
            placeholder="Ask me anything...">
        </textarea>
        <button @click="sendMessage()" :disabled="!inputMessage">
            Send
        </button>
    </div>
</div>

<script>
function chatApp() {
    return {
        messages: [],
        inputMessage: '',
        isTyping: false,

        sendMessage() {
            if (!this.inputMessage.trim()) return;

            // Add user message
            this.messages.push({
                role: 'user',
                content: this.inputMessage,
                timestamp: new Date().toLocaleTimeString()
            });

            const query = this.inputMessage;
            this.inputMessage = '';
            this.isTyping = true;

            // Call API
            fetch('/api/v1/chat/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: query})
            })
            .then(res => res.json())
            .then(data => {
                this.messages.push({
                    role: 'assistant',
                    content: data.response,
                    sources: data.sources,
                    timestamp: new Date().toLocaleTimeString()
                });
                this.isTyping = false;
            });
        }
    }
}
</script>
{% endblock %}
```

---

Due to length constraints, I'll create separate comprehensive files for deployment, API documentation, and complete code. Would you like me to:

1. Generate the complete Django app files (models, views, serializers, etc.)
2. Create deployment scripts for IONOS server
3. Create docker-compose configuration
4. Generate API documentation
5. Create user guides

Which would you like me to prioritize?
