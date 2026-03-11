import re
from pypdf import PdfReader

# Clean extracted text by removing extra whitespace and normalizing spaces
def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Extract text from a PDF policy file, clean it, and store each page with its page number
def extract_pages(file_obj):
    reader = PdfReader(file_obj)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = clean_text(raw_text)
        if text:
            pages.append({
                "page_number": i,
                "text": text
            })
    return pages

def chunk_pages(pages, chunk_size=1200, overlap=200):
    chunks = []
    chunk_id = 0
    for page in pages:
        text = page["text"]
        page_number = page["page_number"]
        start = 0
        step = max(chunk_size - overlap, 1)
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "page_number": page_number,
                    "text": chunk_text
                })
                chunk_id += 1
            start += step
    return chunks

# Process mother policy and internal policy separately
def process_policies(mother_policy_file, internal_policy_file, chunk_size=1200, overlap=200):
    mother_pages = extract_pages(mother_policy_file)
    internal_pages = extract_pages(internal_policy_file)

    mother_chunks = chunk_pages(mother_pages, chunk_size, overlap)
    internal_chunks = chunk_pages(internal_pages, chunk_size, overlap)

    mother_full_text = "\n\n".join(page["text"] for page in mother_pages)
    internal_full_text = "\n\n".join(page["text"] for page in internal_pages)

    return {
        "mother_policy": {
            "full_text": mother_full_text,
            "pages": mother_pages,
            "chunks": mother_chunks
        },
        "internal_policy": {
            "full_text": internal_full_text,
            "pages": internal_pages,
            "chunks": internal_chunks
        }
    }

def build_compliance_comparison_context(mother_policy, internal_policy, max_chars=20000):
    mother_text = mother_policy[:max_chars].strip()
    internal_text = internal_policy[:max_chars].strip()

    context = f"""
=== MOTHER POLICY ===
{mother_text}

=== INTERNAL POLICY ===
{internal_text}
"""
    return context
