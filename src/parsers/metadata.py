import json
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
from pathlib import Path
from langchain_core.documents import Document

from src.parsers.constants import _PRIMITIVES
from src.parsers.chunks import enrich_chunk
from src.spider.content_utils import normalize

@dataclass
class Metadata:
    source: str
    url_slug: str
    title: str
    filename: str = ""
    extension: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

def create_text_source_metadata(source, url_slug, title, filename = "", extension = "") -> dict:
    return Metadata(
        source=source,
        url_slug=url_slug,
        title=title,
        filename=filename,
        extension=extension
    ).to_dict()

def get_keywords_from_path_url(url_path: str) -> list[str]:
    parsed_url = urlparse(url_path)
    hostname = parsed_url.hostname or ""
    subdomain = hostname.split(".")[0] if hostname.count(".") >= 2 else ""
    path_segments = parsed_url.path.strip("/").split("/")
    all_parts = ([subdomain] if subdomain else []) + [s for s in path_segments if s]
    return [normalize(part) for part in all_parts]

def sanitize_metadata(meta: dict) -> dict:
    return {
        k: v if isinstance(v, _PRIMITIVES) else json.dumps(v, default=str)
        for k, v in meta.items()
    }

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