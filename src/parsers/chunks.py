from langchain_core.documents import Document

from src.parsers.constants import _DOCLING_INTERNAL_KEYS
from src.parsers.metadata import get_keywords_from_path_url, sanitize_metadata

def sanitize_chunks(chunks: list[Document]) -> list[Document]:
    for chunk in chunks:
        chunk.metadata = sanitize_metadata({
            k: v for k, v in chunk.metadata.items()
            if k not in _DOCLING_INTERNAL_KEYS
        })
    return chunks

def enrich_chunk(doc: Document) -> Document:
    title = doc.metadata.get("title", "").strip()
    url_slug = doc.metadata.get("url_slug", "").strip()
    headings_raw = doc.metadata.get("headings", "")
    filename = doc.metadata.get("filename", "").strip()
    extension = doc.metadata.get("extension", "").strip()

    page_enrichments = f"[Titlu: {title}]\n" if title else ""
    page_enrichments += f"[Secțiune: {' > '.join(headings_raw) if isinstance(headings_raw, list) else headings_raw}]\n" if headings_raw else ""
    page_enrichments += f"[Cuvinte cheie: {', '.join(get_keywords_from_path_url(url_slug))}]\n" if url_slug else ""
    page_enrichments += f"[Fișier: {filename}]\n" if filename else ""
    page_enrichments += f"[Tip document: {extension}]\n" if extension else ""

    doc.page_content = f"{page_enrichments}{doc.page_content}"

    return doc