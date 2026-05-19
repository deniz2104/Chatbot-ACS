from src.parsers.documents_parser.pdf_parser import process_pdf
from src.parsers.documents_parser.doc_and_docx_parser import process_document
from src.parsers.documents_parser.xls_parser import process_xls
from src.parsers.documents_parser.xlsx_parser import process_xlsx
from src.parsers.entries import DocumentEntry, DocumentType
from langchain_core.documents import Document
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_EXT_TO_DOC_TYPE: dict[str, DocumentType] = {f".{dt.value}": dt for dt in DocumentType}

def parse_document(entry: DocumentEntry) -> list[Document]:
    ext = Path(entry.local_path).suffix.lower()
    doc_type = _EXT_TO_DOC_TYPE.get(ext)
    if doc_type == DocumentType.PDF:
        return process_pdf(entry)
    elif doc_type in (DocumentType.DOC, DocumentType.DOCX):
        return process_document(entry)
    elif doc_type == DocumentType.XLS:
        return process_xls(entry)
    elif doc_type == DocumentType.XLSX:
        return process_xlsx(entry)
    logger.warning("[CHUNKING] Unsupported document extension %r — skipping", ext)
    return []