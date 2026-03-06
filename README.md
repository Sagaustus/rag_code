# BridgeQuest RAG Service

Central Retrieval-Augmented Generation (RAG) backend for BridgeQuest and related Canadian immigration research tools. This repo now hosts a focused Django/DRF service plus supporting Streamlit + ingestion scripts.

---

## 1. What we’re building

**BridgeQuest RAG** is a shared service that:
- Connects to **IONOS AI Model Hub** for embeddings + LLM chat.
- Uses a shared vector collection (e.g. `canadian-immigration`) for Canadian immigration content.
- Exposes a simple HTTP API (starting with `POST /api/chat/`) that both the **BridgeQuest game** (Immigration Consultant) and future **researcher UI** (Perplexity/ChatGPT‑style) can call.
- Will grow to expose collection stats, transparency/traceability, and analytics for scholars.

This separates RAG concerns from the game repo and makes it easier to build multiple UIs on the same knowledge base.

---

## 2. Current directory structure

```text
rag_code/
├── manage.py                 # Django entrypoint
├── rag_system/               # Django project (settings, URLs)
│   ├── settings.py           # INSTALLED_APPS includes rest_framework, rag_core
│   └── urls.py               # /admin/, /api/chat/
├── rag_core/                 # Core RAG app (IONOS client + API view)
│   ├── client.py             # RagClient wrapper around IONOS OpenAI-compatible API
│   └── views.py              # ChatView → POST /api/chat/
├── rag_chat/                 # Chat persistence models (optional)
├── rag_collections/          # Collection metadata (optional)
├── rag_analytics/            # Analytics hooks (optional)
├── docker-compose.yml         # Local Postgres for consistent dev/prod
│
├── src/                      # Streamlit and ingestion utilities
│   ├── chatbot_app.py        # General chat UI (streamlit)
│   ├── rag_gui.py            # Collection search UI
│   ├── rag_gui_with_llm.py   # RAG + LLM answer UI
│   ├── upload_documents_to_ionos.py
│   ├── upload_all_documents.py
│   └── batch_upload.py
│
├── requirements.txt          # Django + DRF + Streamlit + helpers
├── .env.example / .env.template
├── README.md                 # This file
└── *.md                      # Deployment + architecture guides
```

> Note: the older `django_rag/` scaffold has been removed; the Django service lives at the repo root.

---

## 3. Running the components

### 3.1 Configure environment

Create a `.env` (or export vars in your shell) using the IONOS values you already use in the game:

```bash
IONOS_RAG_BASE_URL=https://inference.de-txl.ionos.com
IONOS_RAG_CHAT_ENDPOINT=https://openai.inference.de-txl.ionos.com/v1/chat/completions
IONOS_RAG_API_KEY=...           # IONOS token
IONOS_RAG_MODEL_ID=meta-llama/Llama-3.3-70B-Instruct
IONOS_RAG_INDEX_ID=908cb8ea-58e3-4d87-a41b-05fa91a818d8   # canadian-immigration collection
```

Install deps once:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 3.2 Django RAG service

Start Postgres (local dev, recommended so dev/prod match):

```bash
docker compose up -d
```

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:9000
```

- Chat UI: `http://localhost:9000/chat/`
- API: `POST http://localhost:9000/api/chat/` (stateless)
- API (logged sessions): `POST http://localhost:9000/api/chat/session/`

Note: all `/api/*` endpoints require an API key (set `RAG_API_KEY`) via `Authorization: Bearer <key>`.
The browser UI at `/chat/` uses server-side `/chat/*` proxies so no API key is exposed to the browser.

- API: `POST http://localhost:9000/api/chat/` with JSON body `{ "query": "your question" }`.
- Response: `{ "answer": "...", "error": null }` (or an `error` string on failure).

This is the endpoint the BridgeQuest game (Immigration Consultant) and future UIs will call.

### 3.3 Streamlit tools (`src/`)

You can still use the existing Streamlit apps against the same IONOS collection:

```bash
# Chat-style interface
streamlit run src/chatbot_app.py

# Vector search UI
streamlit run src/rag_gui.py

# RAG + LLM answer viewer
streamlit run src/rag_gui_with_llm.py
```

Document ingestion helpers:

```bash
# Upload documents from local folders into the configured IONOS collection
python src/upload_documents_to_ionos.py

# Batch upload variants
python src/batch_upload.py
python src/upload_all_documents.py
```

---

## 4. Where we are now

As of **March 2026** we have:

- ✅ A dedicated **`canadian-immigration`** collection in IONOS with hundreds of documents.
- ✅ Multi‑workstation ingestion feeding that collection (via the upload scripts).
- ✅ A working Streamlit search interface confirming relevant retrieval.
- ✅ A new **BridgeQuest RAG Django service** (this repo) with:
  - `rag_core.RagClient` that wraps the IONOS OpenAI‑compatible chat API and uses `IONOS_RAG_INDEX_ID`.
  - `POST /api/chat/` endpoint returning plain `{answer, error}`.
- ✅ The BridgeQuest game’s Immigration Consultant updated (in the `bd-game` repo) to talk to IONOS directly via RAG client; next step is to re‑point it to this service.

---

## 5. Next development stages

High‑level roadmap for this repo:

1. **Stabilize BridgeQuest integration**
   - [ ] Add a small HTTP client in the `bd-game` repo that calls `POST /api/chat/` instead of IONOS directly.
   - [ ] Tune the Immigration Consultant prompt for more natural, RAG‑aware answers (fewer hard "I can't confirm" replies; better explanation of uncertainty).

2. **Collections + transparency API**
   - [ ] Add endpoints like `GET /api/collections/` and `GET /api/collections/{id}` that proxy IONOS collection metadata (name, `documentsCount`, createdAt, etc.).
   - [ ] Design a lightweight schema for source metadata (domain, jurisdiction, date, trust level) to support transparency scores.

3. **Researcher / Scholar UI**
   - [ ] Build a Django templates or React front‑end for:
     - Collections dashboard (cards for each collection, stats, filters).
     - Collection detail view (doc list, filters, histograms).
     - Perplexity‑style chat workspace (answer + sources panel + saved threads).
   - [ ] Stream answers from the RAG service for a more LLM‑like feel.

4. **Guardrails and evaluation**
   - [ ] Implement answer‑side guardrails: no personal legal advice, explicit citation of sources, clear statements of uncertainty without being repetitive.
   - [ ] Log questions, selected context docs, and answers (with hashing/PII‑safe logging) for offline evaluation.
   - [ ] Add basic analytics endpoints (query volume, top intents, error rates).

5. **Quality & ops**
   - [ ] Add tests around `rag_core.client.RagClient` and `ChatView`.
   - [ ] Optional: Dockerfile and simple deployment script for IONOS / Heroku.

---

## 6. How other team members should use this repo

- **Game team (BridgeQuest):** treat this as the RAG backend. Call `POST /api/chat/` from the game’s Immigration Consultant and other AI helpers instead of talking to IONOS directly.
- **Research / product team:** iterate on prompts and UX using the Streamlit apps first, then formalize successful patterns into the Django service and future researcher UI.
- **Infra / MLOps:** manage IONOS credentials and collections; ensure `.env` is correct in each environment; monitor usage and costs.

If you’re unsure where to start, run the Django service (`python manage.py runserver 0.0.0.0:9000`) and the `rag_gui.py` Streamlit app side by side to see both the raw collection behavior and the chat API.
