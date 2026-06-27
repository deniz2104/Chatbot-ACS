import logging

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from langchain_core.documents import Document

from src.parsers.constants import _CHUNKER
from src.parsers.entries import DocumentEntry
from src.parsers.error_handlers import parse_error
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

_PDF_OPTIONS = PdfPipelineOptions(
    do_ocr=False,
    do_table_structure=True,
)

_CONVERTER = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=_PDF_OPTIONS)
    }
)

def process_pdf(document_entry: DocumentEntry) -> list[Document]:
    path = document_entry.local_path
    logger.info("[PDF] Converting: %s", path)

    result = None
    with parse_error("PDF", path):
        result = _CONVERTER.convert(path)
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
        logger.warning("[PDF] No chunks produced from %s", path)
        return []

    apply_document_metadata(docs, document_entry, path)
    logger.info("[PDF] Produced %d chunk(s) from %s", len(docs), path)
    return docs
