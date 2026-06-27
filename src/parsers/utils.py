import json
from pathlib import Path
from urllib.parse import urlparse
from langchain_core.documents import Document
from src.parsers.metadata import Metadata
from src.parsers.constants import _PRIMITIVES, _DOCLING_INTERNAL_KEYS
from src.spider.content_utils import normalize

def create_text_source_metadata(source, url_slug, title, filename = "", extension = "") -> dict:
    return Metadata(
        source=source,
        url_slug=url_slug,
        title=title,
        filename=filename,
        extension=extension
    ).to_dict()

def _get_keywords_from_path_url(url_path: str) -> list[str]:
    parsed_url = urlparse(url_path)
    hostname = parsed_url.hostname or ""
    subdomain = hostname.split(".")[0] if hostname.count(".") >= 2 else ""
    path_segments = parsed_url.path.strip("/").split("/")
    all_parts = ([subdomain] if subdomain else []) + [s for s in path_segments if s]
    return [normalize(part) for part in all_parts]

def _sanitize_metadata(meta: dict) -> dict:
    return {
        k: v if isinstance(v, _PRIMITIVES) else json.dumps(v, default=str)
        for k, v in meta.items()
    }

def sanitize_chunks(chunks: list[Document]) -> list[Document]:
    for chunk in chunks:
        chunk.metadata = _sanitize_metadata({
            k: v for k, v in chunk.metadata.items()
            if k not in _DOCLING_INTERNAL_KEYS
        })
    return chunks

def enrich_chunk(doc: Document) -> Document:
    title = doc.metadata.get("title", "").strip()
    url_slug = doc.metadata.get("url_slug", "").strip()
    headings_raw = doc.metadata.get("headings", "")

    if title:
        doc.page_content = f"[Titlu: {title}]\n{doc.page_content}"

    if headings_raw:
        heading_list = json.loads(headings_raw)
        if heading_list:
            doc.page_content = f"[Secțiune: {' > '.join(heading_list)}]\n{doc.page_content}"

    if url_slug:
        keywords = _get_keywords_from_path_url(url_slug)
        if keywords:
            doc.page_content = f"[Cuvinte cheie: {', '.join(keywords)}]\n{doc.page_content}"
    return doc

def apply_document_metadata(docs: list[Document], document_entry, path: str) -> None:
    p = Path(path)
    metadata = create_text_source_metadata(
        source=path,
        url_slug=document_entry.url_slug,
        title=document_entry.title,
        filename=p.name,
        extension=p.suffix,
    )
    for doc in docs:
        doc.metadata.update(metadata)
        enrich_chunk(doc)
