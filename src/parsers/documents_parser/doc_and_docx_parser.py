import logging
import subprocess
from pathlib import Path

from docling.document_converter import DocumentConverter
from langchain_core.documents import Document

from src.parsers.constants import _CHUNKER
from src.parsers.entries import DocumentEntry
from src.parsers.error_handlers import libreoffice_errors, parse_error
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

_CONVERTER = DocumentConverter()

def doc_to_docx(path: str) -> str | None:
    file_path = Path(path)
    output_dir = str(file_path.parent)

    logger.info("[DOC] Converting %s to DOCX", path)

    with libreoffice_errors(path):
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "docx", path, "--outdir", output_dir],
            check=True,
            timeout=60,
        )
        logger.info("[DOC] Conversion successful: %s", file_path.with_suffix(".docx"))
        return str(file_path.with_suffix(".docx"))
    return None


def process_document(document_entry: DocumentEntry) -> list[Document]:
    path = str(document_entry.local_path)
    tmp_path: str | None = None

    if Path(path).suffix == ".doc":
        converted = doc_to_docx(path)
        if converted is not None:
            tmp_path = converted
            path = converted

    logger.info("[DOC] Converting: %s", path)

    result = None
    try:
        with parse_error("DOC", path):
            result = _CONVERTER.convert(path)
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    if result is None:
        return []

    docs = [
        Document(
            page_content=_CHUNKER.contextualize(chunk),
            metadata={**chunk.meta.export_json_dict(), "chunk_type": "text"},
        )
        for chunk in _CHUNKER.chunk(result.document)
        if chunk.text.strip()
    ]

    if not docs:
        logger.warning("[DOC] No chunks produced from %s", path)
        return []

    apply_document_metadata(docs, document_entry, str(document_entry.local_path))
    logger.info("[DOC] Produced %d chunk(s) from %s", len(docs), path)
    return docs
