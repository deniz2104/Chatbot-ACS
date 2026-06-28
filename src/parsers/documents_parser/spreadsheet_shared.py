import logging

from langchain_core.documents import Document

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL
from src.ai_prompts.utils import _extract_ai_text, make_ai_template
from src.parsers.constants import _HEADER_SPLITTER, _TOKEN_SPLITTER
from src.parsers.entries import DocumentEntry
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a spreadsheet-to-text converter optimized for semantic search retrieval.\n\n"
    "The key principle: every output chunk must be self-contained — a reader must be able to "
    "understand it without seeing any other part of the document.\n\n"
    "Analyze the tab-separated sheet data and choose the appropriate format for each sheet:\n\n"
    "FORMAT A — 2D grid with row context AND column context (e.g. timetables, room assignments, "
    "exam schedules, grade matrices — any sheet where a cell's meaning depends on both its row "
    "label and its column label):\n"
    "  Flatten every non-empty cell into a self-contained sentence that repeats ALL relevant "
    "context: the row label, the column label, and the cell value.\n"
    "  Merged cells carry their label forward to every row they span — repeat it explicitly.\n"
    "  Skip empty cells entirely.\n"
    "  Write in the same language as the spreadsheet content (Romanian if the sheet is in Romanian).\n"
    "  Examples for a Romanian timetable:\n"
    "    Grupa 332AB are TD laborator in sala ED307a, luni 12-13.\n"
    "    Seria AB are SSC curs (Conf. Fl. ANTON) in sala EC 105, miercuri 14-15.\n"
    "  Examples for an exam schedule:\n"
    "    Grupa 332AB sustine examenul la Matematica pe 15 ianuarie ora 10, sala PR 001.\n"
    "  Prefix the section with: ## Sheet Name\n\n"
    "FORMAT B — Simple list or table (each row is an independent record with no 2D context "
    "dependency — e.g. student lists, grades, survey results, contact directories):\n"
    "  Output a clean GitHub Flavored Markdown table.\n"
    "  Use the first non-empty row as the header with a separator line (| --- | --- |).\n"
    "  Preserve all cell values exactly as written.\n"
    "  Prefix with: ## Sheet Name\n\n"
    "General rules:\n"
    "  Skip sheets with no meaningful data.\n"
    "  Output ONLY the converted content — no explanations, preamble, or commentary.\n"
    "  If the input contains no meaningful data at all, output an empty string."
)


def sheet_blocks_to_docs(
    sheet_blocks: list[str],
    document_entry: DocumentEntry,
    path: str,
    label: str,
) -> list[Document]:
    template = make_ai_template(_SYSTEM_PROMPT, 4096, content="\n\n".join(sheet_blocks),model=_SONNET_MODEL)
    response = _CLIENT.messages.create(**template.to_dict())
    md = _extract_ai_text(response)

    logger.info(
        "[%s] Converted %s → %d chars (cache_read=%d)",
        label, path, len(md), response.usage.cache_read_input_tokens,
    )

    if not md:
        return []

    header_chunks = _HEADER_SPLITTER.split_text(md)
    docs = _TOKEN_SPLITTER.split_documents(header_chunks)

    apply_document_metadata(docs, document_entry, path)
    logger.info("[%s] Produced %d chunk(s) from %s", label, len(docs), path)
    return docs
