import logging

import openpyxl
from langchain_core.documents import Document

from src.parsers.entries import DocumentEntry
from src.ai_prompts.constants import _CLIENT
from src.ai_prompts.utils import _extract_ai_text, make_ai_template
from src.parsers.utils import apply_document_metadata
from src.parsers.constants import _HEADER_SPLITTER, _TOKEN_SPLITTER

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a precise XLSX spreadsheet-to-Markdown converter.\n\n"
    "Rules:\n"
    "- Convert the tab-separated sheet data you receive into clean GitHub Flavored Markdown\n"
    "- Represent each sheet as a Markdown table, using the first row as the header row "
    "with the separator line (| --- | --- |)\n"
    "- Prefix each sheet's table with a level-2 heading using the sheet name: ## Sheet Name\n"
    "- Preserve all cell content exactly as written, including numbers, dates, and text\n"
    "- Strip any leading/trailing whitespace from cell values\n"
    "- Skip sheets that contain no meaningful data\n"
    "- Do not add any explanation, preamble, or commentary — output ONLY the Markdown\n"
    "- If the input contains no meaningful data at all, output an empty string"
)

def _sheet_to_text(ws) -> str:
    rows = []
    for row in ws.iter_rows(values_only=True):
        cells = [str(cell).strip() if cell is not None else "" for cell in row]
        rows.append("\t".join(cells))
    return "\n".join(rows)


def process_xlsx(document_entry: DocumentEntry) -> list[Document]:
    path = document_entry.local_path
    logger.info("[XLS] Loading file: %s", path)

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        logger.error("[XLS] Could not open workbook %s: %s", path, e)
        return []

    sheet_blocks = []
    for ws in wb.worksheets:
        text = _sheet_to_text(ws)
        if not text.strip():
            logger.debug("[XLS] Skipping empty sheet: %s", ws.title)
            continue
        sheet_blocks.append(f"Sheet: {ws.title}\n{text}")

    wb.close()

    if not sheet_blocks:
        logger.warning("[XLS] No meaningful sheets found in %s", path)
        return []

    template = make_ai_template(_SYSTEM_PROMPT, 4096, content="\n\n".join(sheet_blocks))
    response = _CLIENT.messages.create(**template.to_dict())

    md = _extract_ai_text(response)

    logger.info(
        "[XLS] Converted %s → %d chars (cache_read=%d)",
        path,
        len(md),
        response.usage.cache_read_input_tokens,
    )

    if not md:
        return []

    header_chunks = _HEADER_SPLITTER.split_text(md)
    docs = _TOKEN_SPLITTER.split_documents(header_chunks)

    apply_document_metadata(docs, document_entry, path)
    logger.info("[XLS] Produced %d chunk(s) from %s", len(docs), path)
    return docs