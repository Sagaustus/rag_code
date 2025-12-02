# 🚀 Django RAG System - Quick Start Guide

## 📦 What I'm Building For You

A **production-ready** Django application with:

✅ **Admin Panel** - Non-technical users can upload documents
✅ **Multi-Format Support** - PDFs, DOCX, URLs, Videos, Audio
✅ **Prompt Engineering** - Control prompts with rubrics
✅ **REST API** - Integrate with any frontend
✅ **Chat Interface** - Modern web chat UI
✅ **Background Processing** - Celery for async tasks
✅ **Analytics** - Track usage and performance
✅ **IONOS Integration** - Fully integrated with your setup

---

## ⚡ Quick Deploy (30 Minutes)

### Step 1: Create Django Project

```bash
cd /Users/augustinefarinola/RAG
mkdir django_rag && cd django_rag

# Install Django and dependencies
pip install django djangorestframework celery redis channels psycopg2-binary python-magic PyPDF2 python-docx beautifulsoup4 youtube-transcript-api

# Create project
django-admin startproject config .

# Create apps
python manage.py startapp knowledge_base
python manage.py startapp chatbot
python manage.py startapp prompt_engineering
python manage.py startapp api
```

### Step 2: Configure Settings

I'll create complete configuration files for you in the next steps.

### Step 3: Database Setup

```bash
# Create database
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Step 4: Run Server

```bash
# Development
python manage.py runserver 0.0.0.0:8000

# Production (with gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Step 5: Start Celery (for background tasks)

```bash
# In separate terminal
celery -A config worker -l info
```

---

## 🎯 Key Features Breakdown

### 1. Document Upload Interface (Admin)

**URL:** http://your-server:8000/admin/

**What Users Can Do:**
- ✅ Upload PDFs, DOCX, TXT files via drag & drop
- ✅ Add YouTube videos (auto-extracts transcripts)
- ✅ Add website URLs (auto-scrapes content)
- ✅ Organize docs into collections
- ✅ Tag documents for better organization
- ✅ See processing status in real-time
- ✅ Retry failed uploads
- ✅ Search and filter documents

**No Code Required!** - Just point and click

### 2. Prompt Engineering Dashboard

**URL:** http://your-server:8000/admin/prompt_engineering/

**Control:**
```python
# Example Prompt Template
{
    "name": "Customer Support Agent",
    "system_message": "You are a helpful customer support agent...",
    "user_template": """
Based on the following context:
{context}

Answer this customer question: {question}

Evaluation Criteria:
- Be polite and professional
- Cite sources from knowledge base
- If unsure, say so
    """,
    "rubrics": {
        "politeness": {"weight": 0.3, "description": "Professional tone"},
        "accuracy": {"weight": 0.4, "description": "Correct information"},
        "source_citation": {"weight": 0.2, "description": "Cites sources"},
        "brevity": {"weight": 0.1, "description": "Concise answers"}
    },
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "temperature": 0.7,
    "max_tokens": 1500,
    "num_sources": 3
}
```

**Users Can:**
- Create multiple prompt templates
- A/B test different prompts
- Set rubrics for quality control
- Choose LLM model (Llama 70B, 405B, 8B)
- Control temperature, tokens, sources
- See which prompts perform best
- Version control for prompts

### 3. Chat Interface

**URL:** http://your-server:8000/chat/

**Features:**
- Real-time WebSocket chat
- Conversation history
- Source citations
- User feedback (thumbs up/down)
- Export conversations
- Multi-language support

### 4. REST API

**URL:** http://your-server:8000/api/v1/

**Endpoints:**

```bash
# Upload document
POST /api/v1/documents/upload/
Content-Type: multipart/form-data
{
    "title": "My Document",
    "file": <file>,
    "collection": 1,
    "tags": ["technical", "important"]
}

# Chat
POST /api/v1/chat/
{
    "message": "What is AI ethics?",
    "conversation_id": "abc123",
    "collection_id": 1
}

# List documents
GET /api/v1/documents/?collection=1&status=COMPLETED

# Get conversation history
GET /api/v1/conversations/abc123/messages/
```

### 5. Analytics Dashboard

**URL:** http://your-server:8000/analytics/

**Metrics:**
- Total documents processed
- Most queried topics
- Average response time
- User satisfaction ratings
- Token usage
- Popular prompts
- Error rates

---

## 📁 File Structure I'll Create

```
django_rag/
├── config/
│   ├── settings.py          # ✅ Configuration
│   ├── urls.py              # ✅ URL routing
│   └── celery.py            # ✅ Background tasks
│
├── knowledge_base/
│   ├── models.py            # ✅ Document models
│   ├── admin.py             # ✅ Admin interface
│   ├── views.py             # ✅ Upload views
│   ├── tasks.py             # ✅ Processing tasks
│   └── processors/
│       ├── pdf.py           # ✅ PDF extraction
│       ├── docx.py          # ✅ Word extraction
│       ├── url.py           # ✅ Web scraping
│       └── video.py         # ✅ Video transcripts
│
├── chatbot/
│   ├── models.py            # ✅ Conversation models
│   ├── rag_engine.py        # ✅ RAG logic
│   ├── views.py             # ✅ Chat views
│   └── consumers.py         # ✅ WebSocket
│
├── prompt_engineering/
│   ├── models.py            # ✅ Prompt templates
│   ├── admin.py             # ✅ Prompt management
│   └── validators.py        # ✅ Rubric validators
│
├── api/
│   ├── serializers.py       # ✅ API serializers
│   ├── views.py             # ✅ API views
│   └── permissions.py       # ✅ Access control
│
└── frontend/
    ├── templates/           # ✅ HTML templates
    └── static/              # ✅ CSS, JS
```

---

## 🎨 What the Admin Interface Looks Like

### Document Upload Screen

```
┌─────────────────────────────────────────────────┐
│ 📄 Upload Documents                              │
├─────────────────────────────────────────────────┤
│                                                   │
│  Title: [Customer FAQ Document____________]      │
│                                                   │
│  Collection: [General Knowledge ▼]               │
│                                                   │
│  Document Type:                                   │
│    ○ PDF  ○ Word  ○ Text  ○ URL  ○ Video        │
│                                                   │
│  Upload File:                                     │
│  ┌─────────────────────────────────────┐        │
│  │  Drag & Drop File Here              │        │
│  │  or click to browse                 │        │
│  └─────────────────────────────────────┘        │
│                                                   │
│  OR Enter URL:                                    │
│  [https://example.com/document.pdf_______]       │
│                                                   │
│  Tags: [customer-service] [faq] [+Add]           │
│                                                   │
│  [Cancel]              [Upload & Process]         │
│                                                   │
└─────────────────────────────────────────────────┘
```

### Document List Screen

```
┌──────────────────────────────────────────────────────────┐
│ 📚 Documents (125 total)                    [+ Add New]   │
├──────────────────────────────────────────────────────────┤
│ Search: [____________]  Filter: [All Types ▼] [All ▼]   │
├──────────────────────────────────────────────────────────┤
│ ✓ Customer FAQ v2.0                         | COMPLETED  │
│   PDF • General Knowledge • 2.3 MB          | 2h ago     │
│   [View] [Edit] [Delete] [Re-process]                    │
├──────────────────────────────────────────────────────────┤
│ ⏳ Product Manual 2024                      | PROCESSING │
│   DOCX • Technical Docs • 1.8 MB           | 5m ago     │
│   Progress: ████████░░ 80%                               │
├──────────────────────────────────────────────────────────┤
│ ✗ broken-link.com/doc                       | FAILED     │
│   URL • External Links                      | 1h ago     │
│   Error: 404 Not Found                                   │
│   [Retry] [Edit] [Delete]                                │
└──────────────────────────────────────────────────────────┘
```

### Prompt Engineering Screen

```
┌─────────────────────────────────────────────────────────┐
│ 🎯 Prompt Templates                        [+ Create]    │
├─────────────────────────────────────────────────────────┤
│ ⭐ Customer Support Agent (Default)                      │
│    Model: Llama 3.3 70B • Temp: 0.7 • Tokens: 1500     │
│    Rubrics: 4 criteria • Avg Rating: 4.2/5             │
│    Usage: 1,247 messages                                 │
│    [Edit] [Test] [Duplicate] [View Analytics]           │
├─────────────────────────────────────────────────────────┤
│   Technical Expert                                       │
│    Model: Llama 3.1 405B • Temp: 0.3 • Tokens: 2000    │
│    Rubrics: 5 criteria • Avg Rating: 4.7/5             │
│    Usage: 532 messages                                   │
│    [Edit] [Test] [Set Default]                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Features

- ✅ User authentication & permissions
- ✅ API key management
- ✅ Rate limiting
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ File upload validation
- ✅ Environment variable security

---

## 📊 Database Schema

```sql
-- Collections
CREATE TABLE knowledge_base_collection (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    ionos_collection_id VARCHAR(100) UNIQUE,
    created_by_id INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP,
    is_active BOOLEAN
);

-- Documents
CREATE TABLE knowledge_base_document (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300),
    collection_id INTEGER REFERENCES knowledge_base_collection(id),
    document_type VARCHAR(10),
    file VARCHAR(255),
    url TEXT,
    extracted_text TEXT,
    status VARCHAR(20),
    ionos_document_id VARCHAR(100),
    uploaded_by_id INTEGER REFERENCES auth_user(id),
    uploaded_at TIMESTAMP,
    processed_at TIMESTAMP
);

-- Conversations
CREATE TABLE chatbot_conversation (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE,
    user_id INTEGER REFERENCES auth_user(id),
    collection_id INTEGER REFERENCES knowledge_base_collection(id),
    created_at TIMESTAMP,
    message_count INTEGER,
    total_tokens INTEGER
);

-- Messages
CREATE TABLE chatbot_message (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES chatbot_conversation(id),
    role VARCHAR(10),
    content TEXT,
    retrieved_documents JSONB,
    tokens_used INTEGER,
    rating INTEGER,
    created_at TIMESTAMP
);

-- Prompt Templates
CREATE TABLE prompt_engineering_prompttemplate (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    system_message TEXT,
    user_template TEXT,
    rubrics JSONB,
    model VARCHAR(100),
    temperature FLOAT,
    max_tokens INTEGER,
    num_sources INTEGER,
    is_active BOOLEAN,
    is_default BOOLEAN,
    usage_count INTEGER,
    avg_rating FLOAT
);
```

---

## 🚀 Deployment to IONOS Server

```bash
# 1. Install dependencies
ssh user@your-ionos-server
sudo apt update
sudo apt install python3 python3-pip postgresql redis-server nginx

# 2. Clone/upload project
scp -r django_rag user@server:/var/www/

# 3. Setup virtual environment
cd /var/www/django_rag
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure database
sudo -u postgres createdb rag_db
sudo -u postgres createuser rag_user -P

# 5. Environment variables
nano .env
# Add: IONOS_API_TOKEN, DATABASE_URL, SECRET_KEY

# 6. Migrate database
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# 7. Setup systemd services
# Django service
# Celery service
# See full guide in DEPLOYMENT.md

# 8. Configure Nginx
# Reverse proxy on port 80/443

# 9. Start services
sudo systemctl start django-rag
sudo systemctl start celery-rag

# 10. Access
http://your-server-ip/admin/
```

---

## 💰 Cost & Performance

### Resources Needed:
- **Server:** 2-4 CPU cores, 4-8GB RAM (IONOS VPS works great)
- **Database:** PostgreSQL (included or RDS)
- **Redis:** For Celery (free, minimal resources)
- **Storage:** 20GB+ for documents

### Expected Performance:
- **Document Processing:** 10-50 docs/min (depending on size)
- **Chat Response:** 2-5 seconds
- **Concurrent Users:** 50-100 simultaneous chats
- **API Throughput:** 100+ requests/second

---

## 🎯 Next Steps

### Immediate (I can create now):
1. ✅ Complete Django models file
2. ✅ Admin configuration file
3. ✅ Document processors (PDF, DOCX, URL, Video)
4. ✅ RAG engine implementation
5. ✅ API serializers and views
6. ✅ Settings configuration
7. ✅ Requirements.txt
8. ✅ Deployment scripts

### Priority Files to Create:
**Which would you like first?**

A. **Core Backend** (models, views, processors) - Start coding immediately
B. **Admin Interface** (custom admin panels) - For non-technical users
C. **API Endpoints** (REST API) - For integrations
D. **Deployment Scripts** (systemd, nginx, docker) - For IONOS server
E. **Frontend Templates** (HTML/CSS/JS) - User-facing chat interface

**Or all of them?** I can generate a complete, ready-to-run Django project!

Let me know which you want me to prioritize, and I'll create the complete, production-ready files immediately.
