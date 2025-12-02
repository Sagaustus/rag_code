# 💬 AI Chatbot Application - User Guide

## 🎉 Your Standalone Chatbot is Ready!

A conversational AI chatbot that runs separately from the RAG search interface, with full conversation memory and context awareness.

---

## 🚀 Quick Access

**Chatbot Application:** http://localhost:8503

---

## 🆚 Your Three Applications Compared

| Feature | **Chatbot App** (Port 8503) | **RAG Search** (Port 8502) | **Old Search** (Port 8501) |
|---------|---------------------------|------------------------|----------------------|
| **Interface** | Chat conversation | Q&A with results | Document search only |
| **Conversation Memory** | ✅ Yes | ❌ No | ❌ No |
| **Chat History** | ✅ Persistent | ❌ One-off | ❌ One-off |
| **Context Awareness** | ✅ Remembers previous messages | ❌ Each query independent | ❌ Each query independent |
| **LLM Integration** | ✅ IONOS Llama | ✅ IONOS/OpenAI/Claude | ❌ None |
| **RAG Enabled** | ✅ Yes (toggle on/off) | ✅ Yes | ✅ Retrieval only |
| **Best For** | Natural conversations | Research & analysis | Finding documents |

---

## 💬 Chatbot Features

### ✅ Conversational Interface
- Chat bubble design (like WhatsApp/iMessage)
- Natural back-and-forth conversation
- Friendly and approachable

### ✅ Memory & Context
- Remembers previous messages in the session
- Maintains conversation flow
- Can reference earlier topics

### ✅ RAG Integration
- Retrieves relevant documents for each question
- Shows sources with similarity scores
- Toggle RAG on/off for different conversation modes

### ✅ Session Management
- Chat history persists during session
- Clear chat history button
- Session statistics

### ✅ Flexible Settings
- Choose between multiple LLM models:
  - Llama 3.3 70B (Default)
  - Llama 3.1 405B (Most powerful)
  - Llama 3.1 8B (Fastest)
- Adjust number of sources (1-5)
- Enable/disable RAG

---

## 🎯 How to Use the Chatbot

### Basic Conversation
1. Open http://localhost:8503
2. Type your question in the chat input at the bottom
3. Press Enter or click send
4. Get an AI-generated response with sources

### Example Conversations

#### Single Question
```
You: What is artificial intelligence?

Bot: Artificial intelligence (AI) refers to computer systems
that can perform tasks typically requiring human intelligence,
such as learning, reasoning, and problem-solving. According to
the document on AI fundamentals, AI systems use machine learning
algorithms to improve their performance over time...
📄 Sources: AI_Fundamentals.pdf, Introduction_to_AI.pdf
```

#### Multi-Turn Conversation
```
You: What is machine learning?

Bot: Machine learning is a subset of AI that enables systems
to learn from data without being explicitly programmed...

You: Can you give me an example?

Bot: Based on our previous discussion about machine learning,
a common example is email spam filtering. The system learns
from examples of spam and legitimate emails to automatically
classify new messages...

You: How is that different from deep learning?

Bot: Building on what we discussed, deep learning is a
specialized form of machine learning that uses neural networks
with multiple layers...
```

---

## ⚙️ Settings Explained

### LLM Model Selection
- **Llama 3.3 70B** ⭐ (Recommended)
  - Best balance of quality and speed
  - Great for most conversations

- **Llama 3.1 405B FP8**
  - Highest quality responses
  - Slower but more accurate
  - Best for complex questions

- **Llama 3.1 8B**
  - Fastest responses
  - Good for quick questions
  - Lower quality than 70B

### Sources per Query (1-5)
- **1-2 sources:** Quick, focused answers
- **3 sources:** Default, balanced approach
- **4-5 sources:** Comprehensive, detailed answers

### Use RAG Toggle
- **ON (Default):** Retrieves documents from your knowledge base
  - More accurate, fact-based answers
  - Shows source citations
  - Best for factual questions

- **OFF:** Direct LLM without document retrieval
  - Pure conversational AI
  - No source citations
  - Best for general chat, opinions, or creative tasks

---

## 💡 Sample Conversations to Try

### Research Questions
```
1. "What are the main ethical concerns about AI?"
2. "Tell me more about the bias issue you mentioned"
3. "How can we address these concerns?"
```

### Learning & Education
```
1. "Explain machine learning to me"
2. "What's the difference between supervised and unsupervised learning?"
3. "Can you give me real-world examples?"
```

### Follow-up Questions
```
1. "What is neural network architecture?"
2. "How does that compare to traditional algorithms?"
3. "Which one should I use for image recognition?"
```

---

## 🔧 Technical Details

### Architecture
```
User Message
    ↓
Chatbot checks conversation history
    ↓
Query vector database (if RAG enabled)
    ↓
Retrieve 1-5 relevant documents
    ↓
Build context with:
  - Retrieved documents
  - Last 8 messages from conversation
  - Current user message
    ↓
Send to IONOS Llama LLM
    ↓
Generate response
    ↓
Display with sources
    ↓
Save to conversation history
```

### Conversation Context
- Maintains last **8 messages** (4 exchanges)
- Includes full document context per query
- Resets when you clear chat history

### Memory Persistence
- **Session-based:** Lasts until you close the browser or refresh
- **Not saved:** History doesn't persist between sessions
- **Clear option:** Manual clear via sidebar button

---

## 🎨 Chat Interface Features

### Message Styling
- **Your messages:** Purple/blue bubbles on the right
- **Bot messages:** Gray bubbles on the left
- **Timestamps:** Small gray text below each message
- **Sources:** Blue badges below bot responses

### Visual Feedback
- **Thinking indicator:** "🤔 Thinking..." while processing
- **Source badges:** Clickable document names with scores
- **Clear visual hierarchy:** Easy to follow conversation flow

---

## 🚀 Deployment to IONOS Server

Same process as the RAG application:

```bash
# Upload to server
scp src/chatbot_app.py user@your-server:/home/user/rag-app/

# Run on server
streamlit run chatbot_app.py --server.port 8503 --server.address 0.0.0.0

# Access at
http://your-server-ip:8503
```

Or use systemd service (see DEPLOYMENT_GUIDE.md)

---

## 🎯 Use Cases

### 1. Customer Support
- Answer customer questions about your documents
- Provide consistent, accurate information
- Handle multiple topics in one conversation

### 2. Research Assistant
- Explore complex topics conversationally
- Ask follow-up questions naturally
- Get comprehensive answers with sources

### 3. Internal Knowledge Base
- Employee onboarding
- Policy questions
- Technical documentation queries

### 4. Educational Tool
- Interactive learning
- Contextual explanations
- Progressive topic exploration

---

## 📊 Current System Status

| Component | Status |
|-----------|--------|
| **Chatbot App** | ✅ Running on :8503 |
| **RAG Search** | ✅ Running on :8502 |
| **Knowledge Base** | ✅ 59,583 documents |
| **LLM** | ✅ IONOS Llama 3.3 70B |
| **Conversation Memory** | ✅ Active |

---

## 🎊 Summary

You now have **THREE separate applications**:

1. **Chatbot (Port 8503)** - Conversational AI with memory
2. **RAG Search (Port 8502)** - Q&A with detailed results
3. **Document Search (Port 8501)** - Simple document retrieval

All powered by:
- ✅ IONOS Vector Database (59,583 documents)
- ✅ IONOS Llama LLMs (3.3 70B, 3.1 405B, 3.1 8B)
- ✅ Your existing IONOS API token

**Ready to chat! Open http://localhost:8503 and start a conversation!** 💬
