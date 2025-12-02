"""
Complete script to upload ALL documents from data folder to IONOS AI Model Hub
Handles: PDFs (including subdirectories), HTML files, and JSONL metadata
"""

import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
import PyPDF2
from typing import List, Dict
from bs4 import BeautifulSoup

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

# Get collection ID
COLLECTION_ID = "43327e2b-e7c6-42d3-a7b4-4a0f07f7a8b3"

# Data paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
CURATED_DIR = DATA_DIR / "curated"
RAW_WEB_DIR = DATA_DIR / "raw_web"


def extract_text_from_pdf(pdf_path: Path, max_chars: int = 60000) -> str:
    """Extract text from PDF file with character limit"""
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
        print(f"  Error extracting text: {e}")
        return ""


def extract_text_from_html(html_path: Path, max_chars: int = 60000) -> str:
    """Extract text from HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            if len(text) > max_chars:
                text = text[:max_chars]

            return text.strip()
    except Exception as e:
        print(f"  Error extracting text from HTML: {e}")
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
        print(f"  Error reading JSONL: {e}")
    return metadata_list


def upload_document_to_collection(collection_id: str, name: str, content: str, description: str = "") -> bool:
    """Upload a single document to IONOS collection"""
    if not content or len(content.strip()) == 0:
        print(f"  ⊘ Skipping {name}: Empty content")
        return False

    try:
        # Encode content to base64, handling surrogates and other encoding issues
        content_bytes = content.encode('utf-8', errors='ignore')
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
    except Exception as e:
        print(f"  ✗ {name}: Encoding error")
        return False

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
            print(f"  ✓ {name}")
            return True
        else:
            print(f"  ✗ {name} (Status {response.status_code})")
            return False
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False


def process_all_pdfs(collection_id: str):
    """Process and upload ALL PDF documents including subdirectories"""
    print("\n=== Processing ALL PDFs ===")

    # Get all PDFs recursively
    pdf_files = list(RAW_PDFS_DIR.rglob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")

    success_count = 0
    for idx, pdf_file in enumerate(pdf_files, 1):
        relative_path = pdf_file.relative_to(RAW_PDFS_DIR)
        print(f"[{idx}/{len(pdf_files)}] {relative_path}")

        text = extract_text_from_pdf(pdf_file)
        if text:
            # Create unique name with path info
            name = str(relative_path).replace('/', '_').replace('.pdf', '')
            if upload_document_to_collection(
                collection_id,
                name=name,
                content=text,
                description=f"PDF: {relative_path}"
            ):
                success_count += 1

    print(f"\n✓ PDFs: {success_count}/{len(pdf_files)} uploaded")
    return success_count, len(pdf_files)


def process_all_metadata_files(collection_id: str):
    """Process and upload ALL metadata from JSONL files"""
    print("\n=== Processing ALL Metadata Files ===")
    jsonl_files = list(CURATED_DIR.glob("*.jsonl"))

    print(f"Found {len(jsonl_files)} JSONL files")

    success_count = 0
    total_count = 0

    for jsonl_file in jsonl_files:
        print(f"\n{jsonl_file.name}")
        metadata_list = read_jsonl_metadata(jsonl_file)

        for idx, metadata in enumerate(metadata_list):  # Process ALL entries
            total_count += 1
            # Create text representation
            content = json.dumps(metadata, indent=2)

            # Try to get a meaningful name
            name = f"{jsonl_file.stem}_{idx}"
            if 'title' in metadata:
                name = metadata['title'][:100]
            elif 'name' in metadata:
                name = metadata['name'][:100]

            if upload_document_to_collection(
                collection_id,
                name=name,
                content=content,
                description=f"Metadata: {jsonl_file.name}"
            ):
                success_count += 1

    print(f"\n✓ Metadata: {success_count}/{total_count} uploaded")
    return success_count, total_count


def process_all_html_files(collection_id: str):
    """Process and upload ALL HTML files"""
    print("\n=== Processing ALL HTML Files ===")

    # Get all HTML files recursively
    html_files = list(RAW_WEB_DIR.rglob("*.html"))

    print(f"Found {len(html_files)} HTML files")

    success_count = 0

    for idx, html_file in enumerate(html_files, 1):
        relative_path = html_file.relative_to(RAW_WEB_DIR)
        print(f"[{idx}/{len(html_files)}] {relative_path}")

        text = extract_text_from_html(html_file)
        if text:
            name = str(relative_path).replace('/', '_').replace('.html', '')
            if upload_document_to_collection(
                collection_id,
                name=name,
                content=text,
                description=f"HTML: {relative_path}"
            ):
                success_count += 1

    print(f"\n✓ HTML: {success_count}/{len(html_files)} uploaded")
    return success_count, len(html_files)


def main():
    """Main execution function"""
    print("="*60)
    print(f"UPLOADING ALL DOCUMENTS TO IONOS COLLECTION")
    print(f"Collection ID: {COLLECTION_ID}")
    print(f"Data directory: {DATA_DIR}")
    print("="*60)

    # Track overall statistics
    total_success = 0
    total_files = 0

    # Process all document types
    pdf_success, pdf_total = process_all_pdfs(COLLECTION_ID)
    total_success += pdf_success
    total_files += pdf_total

    meta_success, meta_total = process_all_metadata_files(COLLECTION_ID)
    total_success += meta_success
    total_files += meta_total

    html_success, html_total = process_all_html_files(COLLECTION_ID)
    total_success += html_success
    total_files += html_total

    # Final summary
    print("\n" + "="*60)
    print("UPLOAD SUMMARY")
    print("="*60)
    print(f"Total uploaded: {total_success}/{total_files}")
    print(f"Success rate: {(total_success/total_files*100):.1f}%")
    print("="*60)


if __name__ == "__main__":
    main()
