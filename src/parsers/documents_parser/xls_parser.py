import dataclasses
import logging
import xlrd
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from src.parsers.entries import DocumentEntry
from src.parsers.constants import _TOKENIZER
from src.ai_prompts.constants import _CLIENT
from src.ai_prompts.utils import _extract_ai_text, make_ai_template
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a precise XLS spreadsheet-to-Markdown converter.\n\n"
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

_HEADER_SPLITTER = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "sheet")],
    strip_headers=False,
)

_TOKEN_SPLITTER = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    tokenizer=_TOKENIZER,
    chunk_size=512,
    chunk_overlap=32,
)

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

    try:
        workbook = xlrd.open_workbook(path)
    except xlrd.XLRDError as e:
        logger.error("[XLS] Could not open workbook %s: %s", path, e)
        return []
    except Exception as e:
        logger.error("[XLS] Unexpected error opening %s: %s", path, e)
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

    template = make_ai_template(_SYSTEM_PROMPT, 4096, content="\n\n".join(sheet_blocks))
    response = _CLIENT.messages.create(**dataclasses.asdict(template))

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
