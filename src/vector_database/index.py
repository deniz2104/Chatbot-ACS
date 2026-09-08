import logging

from src.vector_database.vector_db import VectorDatabase
from src.vector_database.constants import _CHUNKS_CHOSEN
from src.vector_database.tokenizer import RomanianTokenizer
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class Bm25Index(VectorDatabase):
    _bm25_index = None

    @classmethod
    def get_bm25_index(cls):
        if cls._bm25_index is None:
            from rank_bm25 import BM25Okapi
            logger.info("[VDB] Building BM25 index...")
            cls._bm25_index = BM25Okapi([RomanianTokenizer.tokenize(doc.page_content) for doc in VectorDatabase.get_documents()])
        return cls._bm25_index

    def __init__(self):
        super().__init__()
        self.get_bm25_index()

    def keyword_search(self, query: str, k: int = _CHUNKS_CHOSEN, urls: set[str] | None = None) -> list[Document]: 
        scores = self.get_bm25_index().get_scores(RomanianTokenizer.tokenize(query)) if self._bm25_index else []
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [VectorDatabase.get_documents()[i] for i in top_indices
                if scores[i] > 0 and (urls is None or VectorDatabase.get_documents()[i].metadata.get("url_slug") in urls)
            ]
        