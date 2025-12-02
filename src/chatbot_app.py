"""
Standalone Conversational Chatbot Application
Built on IONOS RAG System with Chat History
"""

import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
IONOS_API_TOKEN = os.getenv('IONOS_API_TOKEN')
COLLECTION_ID = "43327e2b-e7c6-42d3-a7b4-4a0f07f7a8b3"

# API Configuration
ionos_header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}",
    "Content-Type": "application/json"
}

# Page config
st.set_page_config(
    page_title="AI Chatbot - RAG Powered",
    page_icon="💬",
    layout="centered"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    .user-message {
        background-color: #667eea;
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .assistant-message {
        background-color: #f0f2f6;
        color: #1f1f1f;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .source-badge {
        display: inline-block;
        background-color: #e8f4f8;
        color: #0066cc;
        padding: 0.3rem 0.6rem;
        border-radius: 10px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    .timestamp {
        font-size: 0.7rem;
        color: #999;
        margin-top: 0.3rem;
    }
    .stTextInput input {
        border-radius: 20px;
        padding: 0.8rem 1.2rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Hello! I'm your AI assistant powered by a knowledge base of 59,583+ documents. Ask me anything!",
        "timestamp": datetime.now().strftime("%H:%M"),
        "sources": []
    })

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = []


def query_vector_database(query_text, num_results=3):
    """Query the vector database for relevant documents"""
    try:
        endpoint = f"https://inference.de-txl.ionos.com/collections/{COLLECTION_ID}/query"
        body = {"query": query_text, "limit": num_results}
        response = requests.post(endpoint, json=body, headers=ionos_header, timeout=30)

        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Database error: {e}")
    return None


def decode_content(base64_content):
    """Decode base64 content"""
    try:
        return base64.b64decode(base64_content).decode('utf-8', errors='ignore')
    except:
        return ""


def call_ionos_llm(messages, model="meta-llama/Llama-3.3-70B-Instruct"):
    """Call IONOS AI Model Hub LLM"""
    try:
        headers = {
            "Authorization": f"Bearer {IONOS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500
        }
        response = requests.post(
            "https://openai.inference.de-txl.ionos.com/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=90
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"LLM Error: {e}"


def generate_chatbot_response(user_message, conversation_history, retrieved_docs):
    """Generate chatbot response using RAG"""

    # Build context from retrieved documents
    context_parts = []
    sources = []

    for idx, doc in enumerate(retrieved_docs[:3], 1):
        content = decode_content(doc["document"]["properties"]["content"])
        doc_name = doc["document"]["properties"]["name"]
        score = doc.get("score", 0)

        context_parts.append(f"[Source {idx}: {doc_name}]\n{content[:1500]}")
        sources.append({"name": doc_name, "score": score})

    context = "\n\n".join(context_parts)

    # Build conversation messages with context
    messages = [
        {
            "role": "system",
            "content": f"""You are a helpful AI assistant with access to a knowledge base. Answer questions based on the provided context and conversation history. Be conversational, friendly, and concise.

Context from Knowledge Base:
{context}

Guidelines:
- Use the context to provide accurate answers
- If the answer isn't in the context, say so politely
- Reference sources naturally (e.g., "According to the document on AI Ethics...")
- Maintain conversation flow with previous messages
- Be concise but thorough"""
        }
    ]

    # Add recent conversation history (last 4 exchanges)
    for msg in conversation_history[-8:]:
        if msg["role"] in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    # Generate response
    response = call_ionos_llm(messages)

    return response, sources


def display_message(message):
    """Display a chat message"""
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            {message['content']}
            <div class="timestamp">{message['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            {message['content']}
            <div class="timestamp">{message['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Show sources if available
        if message.get("sources"):
            sources_html = "".join([
                f'<span class="source-badge" title="Score: {src["score"]:.3f}">📄 {src["name"][:30]}...</span>'
                for src in message["sources"][:3]
            ])
            st.markdown(f'<div style="margin-left: 1rem; margin-top: 0.5rem;">{sources_html}</div>',
                       unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<div class="main-header">💬 AI Chatbot Assistant</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Powered by IONOS RAG System</p>',
                unsafe_allow_html=True)

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")

        model_choice = st.selectbox(
            "LLM Model",
            [
                "meta-llama/Llama-3.3-70B-Instruct",
                "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8",
                "meta-llama/Meta-Llama-3.1-8B-Instruct"
            ],
            index=0
        )

        num_sources = st.slider("Sources per query", 1, 5, 3)

        use_rag = st.checkbox("Use RAG (retrieve documents)", value=True,
                             help="When enabled, retrieves relevant documents to answer questions")

        st.markdown("---")

        # Chat statistics
        st.markdown("### 📊 Session Stats")
        st.metric("Messages", len(st.session_state.messages))
        st.metric("Database", "59,583 docs")

        st.markdown("---")

        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Chat history cleared! How can I help you?",
                "timestamp": datetime.now().strftime("%H:%M"),
                "sources": []
            }]
            st.session_state.conversation_context = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 💡 Try asking:")
        st.markdown("""
        - What are AI ethics?
        - Explain machine learning
        - Tell me about AI safety
        - What is deep learning?
        """)

    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Display chat history
    for message in st.session_state.messages:
        display_message(message)

    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Add user message
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp,
            "sources": []
        })

        # Show thinking indicator
        with st.spinner("🤔 Thinking..."):
            if use_rag:
                # Query vector database
                results = query_vector_database(user_input, num_sources)

                if results and "properties" in results and "matches" in results["properties"]:
                    matches = results["properties"]["matches"]

                    if matches:
                        # Generate RAG response
                        response, sources = generate_chatbot_response(
                            user_input,
                            st.session_state.messages[:-1],  # Exclude the message we just added
                            matches
                        )
                    else:
                        response = "I couldn't find relevant information in my knowledge base. Could you rephrase your question?"
                        sources = []
                else:
                    response = "Sorry, I'm having trouble accessing my knowledge base right now."
                    sources = []
            else:
                # Direct LLM without RAG
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant. Be concise and friendly."}
                ]
                for msg in st.session_state.messages[-8:]:
                    if msg["role"] in ["user", "assistant"]:
                        messages.append({"role": msg["role"], "content": msg["content"]})

                response = call_ionos_llm(messages, model_choice)
                sources = []

            # Add assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%H:%M"),
                "sources": sources
            })

        # Rerun to display new messages
        st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 0.8rem;'>
        <p>💬 Conversational AI Chatbot | Powered by IONOS AI Model Hub</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
