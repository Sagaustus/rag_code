"""
Fast batch upload script with progress tracking and resume capability
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
import time

# Load environment variables
load_dotenv()
IONOS_API_TOKEN = os.getenv('IONOS_API_TOKEN')

if not IONOS_API_TOKEN or not IONOS_API_TOKEN.strip():
    raise ValueError("IONOS_API_TOKEN is missing.")

# API Configuration
header = {
    "Authorization": f"Bearer {IONOS_API_TOKEN}",
    "Content-Type": "application/json"
}

COLLECTION_ID = "43327e2b-e7c6-42d3-a7b4-4a0f07f7a8b3"

# Data paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PROGRESS_FILE = BASE_DIR / "upload_progress.json"


def load_progress():
    """Load upload progress"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"uploaded": [], "failed": []}


def save_progress(progress):
    """Save upload progress"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def extract_text_from_pdf(pdf_path: Path, max_chars: int = 60000) -> str:
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                if len(text) > max_chars:
                    break
            return text[:max_chars].strip()
    except:
        return ""


def extract_text_from_html(html_path: Path, max_chars: int = 60000) -> str:
    """Extract text from HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            return text[:max_chars].strip()
    except:
        return ""


def upload_document(name: str, content: str, description: str = "") -> bool:
    """Upload a single document"""
    if not content or len(content.strip()) == 0:
        return False

    try:
        content_bytes = content.encode('utf-8', errors='ignore')
        content_base64 = base64.b64encode(content_bytes).decode("utf-8")
    except:
        return False

    body = {
        "items": [{
            "properties": {
                "name": name[:200],  # Limit name length
                "contentType": "text/plain",
                "content": content_base64,
                "description": description[:500]  # Limit description
            }
        }]
    }

    endpoint = f"https://inference.de-txl.ionos.com/collections/{COLLECTION_ID}/documents"

    try:
        response = requests.put(endpoint, json=body, headers=header, timeout=30)
        return response.status_code == 200
    except:
        return False


def process_pdfs():
    """Process all PDFs"""
    pdf_dir = DATA_DIR / "raw_pdfs"
    pdfs = list(pdf_dir.rglob("*.pdf"))

    progress = load_progress()
    uploaded_names = set(progress["uploaded"])

    print(f"\n📄 Processing {len(pdfs)} PDFs...")

    success = 0
    skipped = 0

    for idx, pdf_path in enumerate(pdfs, 1):
        rel_path = pdf_path.relative_to(pdf_dir)
        name = str(rel_path).replace('/', '_').replace('.pdf', '')

        if name in uploaded_names:
            skipped += 1
            if idx % 20 == 0:
                print(f"  [{idx}/{len(pdfs)}] {success} uploaded, {skipped} skipped")
            continue

        text = extract_text_from_pdf(pdf_path)
        if text and upload_document(name, text, f"PDF: {rel_path}"):
            progress["uploaded"].append(name)
            success += 1
        else:
            progress["failed"].append(name)

        if idx % 20 == 0:
            print(f"  [{idx}/{len(pdfs)}] {success} uploaded, {skipped} skipped")
            save_progress(progress)

    save_progress(progress)
    print(f"  ✓ {success} uploaded, {skipped} skipped")
    return success


def process_html():
    """Process all HTML files"""
    html_dir = DATA_DIR / "raw_web"
    htmls = list(html_dir.rglob("*.html"))

    progress = load_progress()
    uploaded_names = set(progress["uploaded"])

    print(f"\n🌐 Processing {len(htmls)} HTML files...")

    success = 0
    skipped = 0

    for html_path in htmls:
        rel_path = html_path.relative_to(html_dir)
        name = str(rel_path).replace('/', '_').replace('.html', '')

        if name in uploaded_names:
            skipped += 1
            continue

        text = extract_text_from_html(html_path)
        if text and upload_document(name, text, f"HTML: {rel_path}"):
            progress["uploaded"].append(name)
            success += 1
        else:
            progress["failed"].append(name)

    save_progress(progress)
    print(f"  ✓ {success} uploaded, {skipped} skipped")
    return success


def process_metadata():
    """Process all JSONL metadata"""
    jsonl_dir = DATA_DIR / "curated"
    jsonls = list(jsonl_dir.glob("*.jsonl"))

    progress = load_progress()
    uploaded_names = set(progress["uploaded"])

    print(f"\n📊 Processing {len(jsonls)} metadata files...")

    success = 0
    skipped = 0
    total_entries = 0

    for jsonl_path in jsonls:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                if not line.strip():
                    continue

                total_entries += 1
                metadata = json.loads(line)
                name = f"{jsonl_path.stem}_{line_num}"

                if 'title' in metadata:
                    name = metadata['title'][:100]

                if name in uploaded_names:
                    skipped += 1
                    continue

                content = json.dumps(metadata, indent=2)[:60000]
                if upload_document(name, content, f"Metadata: {jsonl_path.name}"):
                    progress["uploaded"].append(name)
                    success += 1
                else:
                    progress["failed"].append(name)

        save_progress(progress)

    print(f"  ✓ {success} uploaded, {skipped} skipped (total {total_entries} entries)")
    return success


def main():
    """Main function"""
    start_time = time.time()

    print("="*60)
    print(f"BATCH UPLOAD TO IONOS COLLECTION")
    print(f"Collection ID: {COLLECTION_ID}")
    print("="*60)

    total_success = 0
    total_success += process_pdfs()
    total_success += process_html()
    total_success += process_metadata()

    elapsed = time.time() - start_time

    print("\n" + "="*60)
    print(f"✓ COMPLETED: {total_success} documents uploaded")
    print(f"⏱ Time: {elapsed/60:.1f} minutes")
    print("="*60)


if __name__ == "__main__":
    main()
