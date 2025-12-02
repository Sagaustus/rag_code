# RAG System - IONOS AI Model Hub

Production-ready Retrieval-Augmented Generation (RAG) system with multiple interfaces and deployment options.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- IONOS AI Model Hub account with API token
- Optional: OpenAI or Anthropic API key for enhanced LLM capabilities

### Installation

1. **Clone/Extract this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your API tokens
```

## 📦 What's Included

### 1. Streamlit Applications (`src/`)

**Chatbot Interface:**
```bash
streamlit run src/chatbot_app.py
```
- Conversational AI with chat history
- RAG-powered responses from your knowledge base
- Modern chat UI

**RAG Search Interface:**
```bash
streamlit run src/rag_gui.py
```
- Document search and retrieval
- Vector similarity search
- Source citations

**Enhanced RAG with LLM:**
```bash
streamlit run src/rag_gui_with_llm.py
```
- Advanced LLM integration
- Context-aware responses
- Multi-model support

### 2. Django Application (`django_rag/`)

Full-featured web application with:
- ✅ Admin panel for document management
- ✅ Multi-format support (PDF, DOCX, URLs, videos, audio)
- ✅ Prompt engineering with rubrics
- ✅ REST API for integrations
- ✅ Chat interface
- ✅ Background processing with Celery
- ✅ Analytics dashboard

**Run Django app:**
```bash
cd django_rag
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Access at: http://localhost:8000/admin/

### 3. Document Upload Tools (`src/`)

**Upload documents to IONOS:**
```bash
python src/upload_documents_to_ionos.py
```

**Batch upload:**
```bash
python src/batch_upload.py
```

## 📚 Documentation

- **[DJANGO_QUICKSTART_GUIDE.md](DJANGO_QUICKSTART_GUIDE.md)** - 30-minute Django deployment
- **[DJANGO_RAG_BLUEPRINT.md](DJANGO_RAG_BLUEPRINT.md)** - Architecture overview
- **[CHATBOT_GUIDE.md](CHATBOT_GUIDE.md)** - Chat interface setup
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md)** - Heroku-specific guide
- **[LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md)** - LLM configuration

## 🏗️ Architecture

```
RAG_Export/
├── src/                          # Streamlit apps & utilities
│   ├── chatbot_app.py           # Chat interface
│   ├── rag_gui.py               # Search interface
│   ├── rag_gui_with_llm.py      # Enhanced RAG
│   ├── upload_documents_to_ionos.py
│   └── data/                     # Sample documents
│
├── django_rag/                   # Django application
│   ├── config/                   # Settings & URLs
│   ├── knowledge_base/           # Document management
│   ├── chatbot/                  # Chat functionality
│   └── prompt_engineering/       # Prompt templates
│
├── django_rag_app/              # Additional Django components
│
└── Documentation files (.md)
```

## 🔑 Environment Variables

Required in `.env`:
```bash
IONOS_API_TOKEN=your_token_here
```

Optional:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

## 🌐 Deployment Options

### Option 1: Local Development
Run Streamlit or Django locally (see Quick Start)

### Option 2: IONOS Cloud Server
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Option 3: Heroku
See [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md)

## 🔒 Security Notes

- Never commit `.env` file with real tokens
- Use `.env.example` as template
- Rotate API keys regularly
- Enable rate limiting in production

## 📊 Features

- ✅ Multi-format document processing (PDF, DOCX, URLs, videos)
- ✅ Vector similarity search with IONOS
- ✅ Multiple LLM options (Llama 3.3, GPT-4, Claude)
- ✅ Chat history and conversation management
- ✅ Admin interface for non-technical users
- ✅ REST API for integrations
- ✅ Background task processing
- ✅ Production-ready deployment configs

## 🤝 Support

For issues or questions:
1. Check documentation files
2. Review `.env.example` for configuration
3. Ensure IONOS API token is valid
4. Verify dependencies are installed

## 📝 License

[Add your license information]

---

**Built with IONOS AI Model Hub** 🚀
