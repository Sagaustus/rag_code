"""
Script to extract documents from local data folder and upload to IONOS AI Model Hub
"""

import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
import PyPDF2
from typing import List, Dict

# Load environment variables
load_dotenv()
IONOS_API_TOKEN = os.getenv('IONOS_API_TOKEN')

if not IONOS_API_TOKEN or not IONOS_API_TOKEN.strip():
    raise ValueError("IONOS_API_TOKEN is missing. Set it in your environment or a .env file.")

# API Configuration
header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}",
    "Content-Type": "application/json"
}

# Get collection ID from command line or use default
COLLECTION_ID = "43327e2b-e7c6-42d3-a7b4-4a0f07f7a8b3"  # Replace with your actual collection ID

# Data paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
CURATED_DIR = DATA_DIR / "curated"
RAW_WEB_DIR = DATA_DIR / "raw_web"


def extract_text_from_pdf(pdf_path: Path, max_chars: int = 60000) -> str:
    """Extract text from PDF file with character limit (keeping well under 65535 bytes)"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                if len(text) > max_chars:
                    text = text[:max_chars]
                    break
            return text.strip()
    except Exception as e:
        print(f"Error extracting text from {pdf_path.name}: {e}")
        return ""


def read_jsonl_metadata(jsonl_path: Path) -> List[Dict]:
    """Read metadata from JSONL file"""
    metadata_list = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    metadata_list.append(json.loads(line))
    except Exception as e:
        print(f"Error reading {jsonl_path.name}: {e}")
    return metadata_list


def read_text_file(file_path: Path, max_chars: int = 60000) -> str:
    """Read text content from file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if len(content) > max_chars:
                content = content[:max_chars]
            return content.strip()
    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return ""


def upload_document_to_collection(collection_id: str, name: str, content: str, description: str = "") -> bool:
    """Upload a single document to IONOS collection"""
    if not content or len(content.strip()) == 0:
        print(f"Skipping {name}: Empty content")
        return False

    # Encode content to base64
    content_base64 = base64.b64encode(content.encode('utf-8')).decode("utf-8")

    body = {
        "items": [{
            "properties": {
                "name": name,
                "contentType": "text/plain",
                "content": content_base64,
                "description": description
            }
        }]
    }

    endpoint = f"https://inference.de-txl.ionos.com/collections/{collection_id}/documents"

    try:
        response = requests.put(endpoint, json=body, headers=header)
        if response.status_code == 200:
            print(f"✓ Uploaded: {name}")
            return True
        else:
            print(f"✗ Failed to upload {name}: Status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error uploading {name}: {e}")
        return False


def process_pdfs(collection_id: str, limit: int = None):
    """Process and upload PDF documents"""
    print("\n=== Processing PDFs ===")
    pdf_files = list(RAW_PDFS_DIR.glob("*.pdf"))

    if limit:
        pdf_files = pdf_files[:limit]

    success_count = 0
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        text = extract_text_from_pdf(pdf_file)
        if text:
            if upload_document_to_collection(
                collection_id,
                name=pdf_file.stem,
                content=text,
                description=f"PDF document: {pdf_file.name}"
            ):
                success_count += 1

    print(f"Successfully uploaded {success_count}/{len(pdf_files)} PDFs")


def process_metadata_files(collection_id: str):
    """Process and upload metadata from JSONL files"""
    print("\n=== Processing Metadata Files ===")
    jsonl_files = list(CURATED_DIR.glob("*.jsonl"))

    success_count = 0
    total_count = 0

    for jsonl_file in jsonl_files:
        print(f"\nProcessing {jsonl_file.name}...")
        metadata_list = read_jsonl_metadata(jsonl_file)

        for idx, metadata in enumerate(metadata_list[:5]):  # Limit to 5 per file for testing
            total_count += 1
            # Create a text representation of the metadata
            content = json.dumps(metadata, indent=2)
            name = f"{jsonl_file.stem}_{idx}"

            if 'title' in metadata:
                name = metadata['title'][:100]  # Limit name length

            if upload_document_to_collection(
                collection_id,
                name=name,
                content=content,
                description=f"Metadata from {jsonl_file.name}"
            ):
                success_count += 1

    print(f"Successfully uploaded {success_count}/{total_count} metadata entries")


def process_web_content(collection_id: str):
    """Process and upload web content"""
    print("\n=== Processing Web Content ===")

    success_count = 0
    total_count = 0

    # Process essays
    essays_dir = RAW_WEB_DIR / "essays"
    if essays_dir.exists():
        for text_file in essays_dir.glob("*.txt"):
            total_count += 1
            content = read_text_file(text_file)
            if content:
                if upload_document_to_collection(
                    collection_id,
                    name=text_file.stem,
                    content=content,
                    description=f"Essay: {text_file.name}"
                ):
                    success_count += 1

    # Process SEP content
    sep_dir = RAW_WEB_DIR / "sep"
    if sep_dir.exists():
        for text_file in sep_dir.glob("*.txt"):
            total_count += 1
            content = read_text_file(text_file)
            if content:
                if upload_document_to_collection(
                    collection_id,
                    name=text_file.stem,
                    content=content,
                    description=f"SEP entry: {text_file.name}"
                ):
                    success_count += 1

    print(f"Successfully uploaded {success_count}/{total_count} web content files")


def main():
    """Main execution function"""
    print(f"Starting document upload to collection: {COLLECTION_ID}")
    print(f"Data directory: {DATA_DIR}")

    # Process different document types
    # Uncomment the functions below to process more documents
    process_pdfs(COLLECTION_ID, limit=10)  # Process 10 PDFs
    process_metadata_files(COLLECTION_ID)
    process_web_content(COLLECTION_ID)

    print("\n=== Upload Complete ===")


if __name__ == "__main__":
    main()
