"""
Complete RAG GUI Application with LLM Integration
Supports: IONOS LLMs, OpenAI, Anthropic Claude, or Local LLMs
"""

import streamlit as st
import requests
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
IONOS_API_TOKEN = os.getenv('IONOS_API_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

COLLECTION_ID = "43327e2b-e7c6-42d3-a7b4-4a0f07f7a8b3"

# API Configuration
ionos_header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}",
    "Content-Type": "application/json"
}

# Page config
st.set_page_config(
    page_title="RAG System - AI Powered",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .answer-box {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2ca02c;
        margin: 1rem 0;
    }
    .source-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 3px solid #1f77b4;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def get_collection_stats():
    """Get collection statistics"""
    try:
        endpoint = f"https://inference.de-txl.ionos.com/collections/{COLLECTION_ID}"
        response = requests.get(endpoint, headers=ionos_header, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data["properties"]["name"],
                "document_count": data["properties"]["documentsCount"],
                "embedding_model": data["properties"]["embedding"]["model"]
            }
    except:
        pass
    return None


def query_vector_database(query_text, num_results=3):
    """Query the vector database for relevant documents"""
    try:
        endpoint = f"https://inference.de-txl.ionos.com/collections/{COLLECTION_ID}/query"
        body = {"query": query_text, "limit": num_results}
        response = requests.post(endpoint, json=body, headers=ionos_header, timeout=30)

        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error querying database: {e}")
    return None


def decode_content(base64_content):
    """Decode base64 content"""
    try:
        return base64.b64decode(base64_content).decode('utf-8')
    except:
        return "Unable to decode content"


def call_openai_llm(messages, model="gpt-3.5-turbo"):
    """Call OpenAI API"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling OpenAI: {e}"
    return None


def call_anthropic_llm(messages, model="claude-3-5-sonnet-20241022"):
    """Call Anthropic Claude API"""
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        # Convert messages format
        system_msg = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        body = {
            "model": model,
            "max_tokens": 1024,
            "messages": user_messages
        }
        if system_msg:
            body["system"] = system_msg

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
    except Exception as e:
        return f"Error calling Claude: {e}"
    return None


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
            return f"Error: Status {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error calling IONOS LLM: {e}"
    return None


def generate_rag_answer(query, retrieved_docs, llm_provider, llm_model):
    """Generate answer using RAG pipeline"""

    # Build context from retrieved documents
    context_parts = []
    for idx, doc in enumerate(retrieved_docs, 1):
        content = decode_content(doc["document"]["properties"]["content"])
        doc_name = doc["document"]["properties"]["name"]
        context_parts.append(f"[Document {idx}: {doc_name}]\n{content[:2000]}\n")

    context = "\n".join(context_parts)

    # Create prompt
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Answer questions based on the provided context documents. If the answer is not in the context, say so. Be concise and accurate."
        },
        {
            "role": "user",
            "content": f"""Context Documents:
{context}

Question: {query}

Please provide a clear, accurate answer based on the context documents above. Cite which document(s) you're referencing."""
        }
    ]

    # Call appropriate LLM
    if llm_provider == "IONOS AI Model Hub":
        return call_ionos_llm(messages, llm_model)
    elif llm_provider == "OpenAI":
        return call_openai_llm(messages, llm_model)
    elif llm_provider == "Anthropic Claude":
        return call_anthropic_llm(messages, llm_model)
    else:
        return "No LLM configured. Please select a provider."


def main():
    # Header
    st.markdown('<div class="main-header">🤖 Complete RAG System</div>', unsafe_allow_html=True)
    st.markdown("### Ask questions and get AI-powered answers from your documents")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # LLM Provider selection
        llm_provider = st.selectbox(
            "LLM Provider",
            ["IONOS AI Model Hub", "OpenAI", "Anthropic Claude"],
            help="Select your LLM provider"
        )

        # Model selection based on provider
        if llm_provider == "IONOS AI Model Hub":
            llm_model = st.selectbox(
                "Model",
                [
                    "meta-llama/Llama-3.3-70B-Instruct",
                    "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct",
                    "mistralai/Mistral-Nemo-Instruct-2407"
                ],
                index=0
            )
            st.success("✅ Using your IONOS API token")
        elif llm_provider == "OpenAI":
            llm_model = st.selectbox(
                "Model",
                ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                index=2
            )
            if not OPENAI_API_KEY:
                st.error("⚠️ Add OPENAI_API_KEY to .env")
        elif llm_provider == "Anthropic Claude":
            llm_model = st.selectbox(
                "Model",
                ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                index=0
            )
            if not ANTHROPIC_API_KEY:
                st.error("⚠️ Add ANTHROPIC_API_KEY to .env")

        num_sources = st.slider("Sources to retrieve", 1, 10, 3)

        st.markdown("---")
        st.header("📊 Collection Stats")

        stats = get_collection_stats()
        if stats:
            st.metric("Documents", f"{stats['document_count']:,}")
            st.caption(f"Model: {stats['embedding_model']}")

        st.markdown("---")
        st.markdown("### 💡 Sample Questions")
        st.markdown("""
        - What are the ethical implications of AI?
        - Explain machine learning
        - What is artificial intelligence?
        - AI safety concerns
        """)

    # Main content
    query = st.text_area(
        "❓ Your Question:",
        placeholder="Ask anything about your documents...",
        height=100,
        help="Enter your question and the AI will search relevant documents and generate an answer"
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_button = st.button("🔍 Ask AI", type="primary", use_container_width=True)
    with col2:
        retrieval_only = st.checkbox("Retrieval only", help="Skip LLM generation")

    if search_button and query:
        with st.spinner("🔎 Searching documents..."):
            results = query_vector_database(query, num_sources)

            if results and "properties" in results and "matches" in results["properties"]:
                matches = results["properties"]["matches"]

                if matches:
                    if not retrieval_only:
                        with st.spinner(f"🤖 Generating answer with {llm_provider}..."):
                            answer = generate_rag_answer(query, matches, llm_provider, llm_model)

                            # Display answer
                            st.markdown("### 💬 AI Answer")
                            st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

                    # Display sources
                    st.markdown("---")
                    st.markdown(f"### 📚 Source Documents ({len(matches)} found)")

                    for idx, match in enumerate(matches, 1):
                        doc = match["document"]["properties"]
                        similarity = match.get("score", 0)

                        with st.expander(f"📄 Source {idx}: {doc['name']} (Score: {similarity:.3f})"):
                            content = decode_content(doc['content'])

                            st.markdown(f"**Document:** {doc['name']}")
                            if doc.get('description'):
                                st.markdown(f"**Type:** {doc['description']}")

                            st.text_area(
                                "Content:",
                                content[:1500] + ("..." if len(content) > 1500 else ""),
                                height=200,
                                key=f"source_{idx}"
                            )

                            st.download_button(
                                "📥 Download",
                                content,
                                file_name=f"{doc['name']}.txt",
                                key=f"dl_{idx}"
                            )
                else:
                    st.warning("No relevant documents found.")
            else:
                st.error("Search failed. Please try again.")

    elif search_button and not query:
        st.warning("Please enter a question.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 Complete RAG System | IONOS Vector DB + LLM | Powered by AI</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
