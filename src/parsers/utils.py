import json
from pathlib import Path
from langchain_core.documents import Document
from src.parsers.metadata import Metadata
from src.parsers.constants import _PRIMITIVES

def create_ai_metadata(source, url_slug, title, filename = "", extension = "") -> dict:
    return Metadata(
        source=source,
        url_slug=url_slug,
        title=title,
        filename=filename,
        extension=extension
    ).to_dict()

def _sanitize_metadata(meta: dict) -> dict:
    return {
        k: v if isinstance(v, _PRIMITIVES) else json.dumps(v, default=str)
        for k, v in meta.items()
    }

def sanitize_chunks(chunks: list[Document]) -> list[Document]:
    for chunk in chunks:
        chunk.metadata = _sanitize_metadata(chunk.metadata)
    return chunks

def apply_document_metadata(docs: list[Document], document_entry, path: str) -> None:
    p = Path(path)
    metadata = create_ai_metadata(
        source=path,
        url_slug=document_entry.url_slug,
        title=document_entry.title,
        filename=p.name,
        extension=p.suffix,
    )
    for doc in docs:
        doc.metadata.update(metadata)
