import logging

from langchain_core.documents import Document

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL
from src.ai_prompts.utils import _extract_ai_text, make_ai_template
from src.parsers.constants import _HEADER_SPLITTER, _TOKEN_SPLITTER
from src.parsers.entries import DocumentEntry
from src.parsers.utils import apply_document_metadata

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a precise spreadsheet-to-Markdown converter.\n\n"
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
