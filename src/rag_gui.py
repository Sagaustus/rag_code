"""
RAG GUI Application for IONOS Vector Database
Deploy this on your IONOS Cloud Server
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
COLLECTION_ID = "43327e2b-e7c6-42d3-a7b4-4a0f07f7a8b3"

# API Configuration
header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}",
    "Content-Type": "application/json"
}

# Page config
st.set_page_config(
    page_title="RAG Search Interface",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .result-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .similarity-score {
        color: #28a745;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def get_collection_stats():
    """Get collection statistics"""
    try:
        endpoint = f"https://inference.de-txl.ionos.com/collections/{COLLECTION_ID}"
        response = requests.get(endpoint, headers=header, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data["properties"]["name"],
                "description": data["properties"]["description"],
                "document_count": data["properties"]["documentsCount"],
                "total_tokens": data["properties"]["totalTokens"],
                "embedding_model": data["properties"]["embedding"]["model"],
                "chunking_enabled": data["properties"]["chunking"]["enabled"]
            }
    except Exception as e:
        st.error(f"Error fetching collection stats: {e}")
    return None


def query_documents(query_text, num_results=5):
    """Query the vector database"""
    try:
        endpoint = f"https://inference.de-txl.ionos.com/collections/{COLLECTION_ID}/query"
        body = {
            "query": query_text,
            "limit": num_results
        }
        response = requests.post(endpoint, json=body, headers=header, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Query failed with status {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error querying documents: {e}")
        return None


def decode_content(base64_content):
    """Decode base64 content"""
    try:
        return base64.b64decode(base64_content).decode('utf-8')
    except:
        return "Unable to decode content"


def main():
    # Header
    st.markdown('<div class="main-header">🔍 RAG Search Interface</div>', unsafe_allow_html=True)
    st.markdown("### Query your IONOS Vector Database Collection")

    # Sidebar - Collection Stats
    with st.sidebar:
        st.header("📊 Collection Statistics")

        if st.button("🔄 Refresh Stats"):
            st.rerun()

        stats = get_collection_stats()
        if stats:
            st.markdown(f"""
            <div class="stat-box">
                <h4>{stats['name']}</h4>
                <p><strong>Documents:</strong> {stats['document_count']:,}</p>
                <p><strong>Total Tokens:</strong> {stats['total_tokens']:,}</p>
                <p><strong>Model:</strong> {stats['embedding_model']}</p>
                <p><strong>Chunking:</strong> {'Enabled' if stats['chunking_enabled'] else 'Disabled'}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Unable to fetch collection stats")

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        This interface allows you to perform semantic searches
        on your document collection using natural language queries.
        """)

    # Main content
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Enter your search query:",
            placeholder="e.g., What are the ethical implications of AI?",
            help="Enter a natural language question or search term"
        )

    with col2:
        num_results = st.number_input(
            "Results:",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of results to retrieve"
        )

    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    # Search functionality
    if search_button and query:
        with st.spinner("Searching..."):
            results = query_documents(query, num_results)

            if results and "properties" in results and "matches" in results["properties"]:
                matches = results["properties"]["matches"]

                if matches:
                    st.success(f"Found {len(matches)} relevant documents")
                    st.markdown("---")

                    # Display results
                    for idx, match in enumerate(matches, 1):
                        doc = match["document"]["properties"]
                        similarity = match.get("score", "N/A")

                        with st.expander(f"📄 Result {idx}: {doc['name']}", expanded=(idx == 1)):
                            col_a, col_b = st.columns([3, 1])

                            with col_a:
                                st.markdown(f"**Document:** {doc['name']}")
                                if doc.get('description'):
                                    st.markdown(f"**Description:** {doc['description']}")

                            with col_b:
                                st.markdown(f"**Similarity:** <span class='similarity-score'>{similarity:.4f}</span>",
                                          unsafe_allow_html=True)

                            st.markdown("---")

                            # Decode and display content
                            content = decode_content(doc['content'])

                            # Show preview
                            preview_length = 500
                            if len(content) > preview_length:
                                st.text_area(
                                    "Content Preview:",
                                    content[:preview_length] + "...",
                                    height=200,
                                    key=f"preview_{idx}"
                                )

                                if st.button(f"Show Full Content", key=f"full_{idx}"):
                                    st.text_area(
                                        "Full Content:",
                                        content,
                                        height=400,
                                        key=f"full_content_{idx}"
                                    )
                            else:
                                st.text_area(
                                    "Content:",
                                    content,
                                    height=200,
                                    key=f"content_{idx}"
                                )

                            # Download button
                            st.download_button(
                                label="📥 Download Document",
                                data=content,
                                file_name=f"{doc['name']}.txt",
                                mime="text/plain",
                                key=f"download_{idx}"
                            )
                else:
                    st.warning("No matching documents found. Try a different query.")
            else:
                st.error("No results returned from the query.")

    elif search_button and not query:
        st.warning("Please enter a search query.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Powered by IONOS AI Model Hub | Vector Database Search Interface</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
