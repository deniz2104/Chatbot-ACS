import logging

from langchain_core.documents import Document

from src.ai_prompts.query_rewriter import rewrite_query
from src.vector_database.query import query

logger = logging.getLogger(__name__)

def handle_query(question: str) -> list[Document]:
    rewritten = rewrite_query(question)

    docs = query(rewritten)
    if docs:
        return docs

    urls = resolve_urls(rewritten)
    if not urls:
        return []

    uncrawled = [url for url in urls if url not in _load_crawled_urls()]
    if uncrawled:
        _crawl(uncrawled)
        docs = query(rewritten)

    return docs
