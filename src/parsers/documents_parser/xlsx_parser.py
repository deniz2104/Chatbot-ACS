import logging
from langchain_docling import DoclingLoader
from langchain_core.documents import Document
from openpyxl import load_workbook
from src.parsers.constants import _EXPORT_TYPE, _CHUNKER
from src.parsers.entries import DocumentEntry
from src.parsers.utils import apply_document_metadata
from pathlib import Path

logger = logging.getLogger(__name__)

def split_xlsx_by_sheet(path: str) -> list[tuple[int, str]]:
    wb = load_workbook(path, read_only=True, data_only=True)
    base = Path(path)
    sheet_files = []
    for idx, sheet_name in enumerate(wb.sheetnames, start=1):
        wb_single = load_workbook(path, data_only=True)
        for name in [n for n in wb_single.sheetnames if n != sheet_name]:
            del wb_single[name]
        out_path = str(base.parent / f"{base.stem}_sheet{idx}.xlsx")
        wb_single.save(out_path)
        sheet_files.append((idx, out_path))
        logger.info("[XLS] Split sheet %d (%s) -> %s", idx, sheet_name, out_path)
    wb.close()
    
    return sheet_files


def process_xlsx(document_entry: DocumentEntry) -> list[Document]:
    path = document_entry.local_path

    sheet_files = split_xlsx_by_sheet(path)
    docs = []

    for sheet_idx, sheet_path in sheet_files:
        logger.info("[XLS] Loading sheet %d: %s", sheet_idx, sheet_path)
        loader = DoclingLoader(
            file_path=sheet_path,
            export_type=_EXPORT_TYPE,
            chunker=_CHUNKER,
        )
        sheet_docs = loader.load()
        logger.info("[XLS] Sheet %d: %d chunk(s)", sheet_idx, len(sheet_docs))

        for doc in sheet_docs:
            if not doc.page_content.strip():
                logger.warning("[XLS] Empty chunk in sheet %d — skipping", sheet_idx)
                continue
            doc.metadata["sheet_index"] = sheet_idx
            docs.append(doc)

    apply_document_metadata(docs, document_entry, path)
    logger.info("[XLS] Produced %d chunk(s) from %s", len(docs), path)
    return docs