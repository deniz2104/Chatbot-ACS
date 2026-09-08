import logging

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from langchain_core.documents import Document

from src.parsers.constants import _CHUNKER, _SEPARATOR
from src.parsers.entries import PageEntry
from src.parsers.chunks import enrich_chunk
from src.parsers.metadata import create_text_source_metadata

logger = logging.getLogger(__name__)

_CONVERTER = DocumentConverter()

def process_markdown(page_entry: PageEntry) -> tuple[list[Document], list[Document]]:
    base_metadata = create_text_source_metadata(
        source=page_entry.url_slug,
        url_slug=page_entry.url_slug,
        title=page_entry.title,
    )

    result = _CONVERTER.convert_string(content=page_entry.text, format=InputFormat.MD)
    text_docs = [
        enrich_chunk(Document(
            page_content=_CHUNKER.contextualize(chunk),
            metadata={**chunk.meta.export_json_dict(), **base_metadata, "chunk_type": "text"},
        ))
        for chunk in _CHUNKER.chunk(result.document)
        if chunk.text.strip()
    ]

    table_docs = []
    for raw in page_entry.tables.split(_SEPARATOR):
        if raw:
            table_docs.append(enrich_chunk(Document(
                page_content=raw,
                metadata={**base_metadata, "chunk_type": "table"},
            )))

    logger.info(
        "[MARKDOWN] %d text chunk(s), %d table(s) from: %s",
        len(text_docs), len(table_docs), page_entry.url_slug,
    )
    return text_docs, table_docs
