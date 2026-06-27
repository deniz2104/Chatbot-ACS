import logging

import xlrd
from langchain_core.documents import Document

from src.parsers.documents_parser.spreadsheet_shared import sheet_blocks_to_docs
from src.parsers.entries import DocumentEntry
from src.parsers.error_handlers import parse_error

logger = logging.getLogger(__name__)

_LABEL = "XLS"


def _sheet_to_text(sheet: xlrd.sheet.Sheet) -> str:
    rows = []
    for row_idx in range(sheet.nrows):
        row = [str(sheet.cell(row_idx, col_idx).value).strip() for col_idx in range(sheet.ncols)]
        rows.append("\t".join(row))
    return "\n".join(rows)


def _is_meaningful_sheet(sheet: xlrd.sheet.Sheet) -> bool:
    return any(
        sheet.cell(r, c).value not in ("", None)
        for r in range(sheet.nrows)
        for c in range(sheet.ncols)
    )


def process_xls(document_entry: DocumentEntry) -> list[Document]:
    path = document_entry.local_path
    logger.info("[XLS] Loading file: %s", path)

    workbook = None
    with parse_error(_LABEL, path):
        workbook = xlrd.open_workbook(path)
    if workbook is None:
        return []

    sheet_blocks = []
    for sheet in workbook.sheets():
        if not _is_meaningful_sheet(sheet):
            logger.debug("[XLS] Skipping empty sheet: %s", sheet.name)
            continue
        sheet_blocks.append(f"Sheet: {sheet.name}\n{_sheet_to_text(sheet)}")

    if not sheet_blocks:
        logger.warning("[XLS] No meaningful sheets found in %s", path)
        return []

    return sheet_blocks_to_docs(sheet_blocks, document_entry, path, _LABEL)
