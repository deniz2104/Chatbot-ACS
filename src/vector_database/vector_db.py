import logging

import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.vector_database.constants import EMBED_MODEL, VECTOR_STORE_DIR

logger = logging.getLogger(__name__)

COLLECTION_CURRENT = "current"
COLLECTION_PREVIOUS = "previous"


class _VectorDB:
    def __init__(self) -> None:
        self._client: ClientAPI | None = None
        self._embeddings = None
        self._vs_current: Chroma | None = None
        self._vs_previous: Chroma | None = None

    def _get_client(self) -> ClientAPI:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=VECTOR_STORE_DIR,
                settings=Settings(allow_reset=True),
            )
        return self._client

    def _get_embeddings(self):
        if self._embeddings is None:
            logger.info("Loading embedding model: %s", EMBED_MODEL)
            self._embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        return self._embeddings

    def _get_vectorstore(self) -> Chroma:
        if self._vs_current is None:
            self._vs_current = Chroma(
                client=self._get_client(),
                collection_name=COLLECTION_CURRENT,
                embedding_function=self._get_embeddings(),
                collection_metadata={"hnsw:space": "cosine"},
            )
        return self._vs_current

    def _get_previous_vectorstore(self) -> Chroma:
        if self._vs_previous is None:
            self._vs_previous = Chroma(
                client=self._get_client(),
                collection_name=COLLECTION_PREVIOUS,
                embedding_function=self._get_embeddings(),
                collection_metadata={"hnsw:space": "cosine"},
            )
        return self._vs_previous

    def promote_current_to_previous(self) -> None:
        vs_current = self._get_vectorstore()
        data = vs_current._collection.get(include=["documents", "metadatas", "embeddings"])

        self.delete_previous()
        vs_previous = self._get_previous_vectorstore()

        documents = data["documents"]
        embeddings = data["embeddings"]
        if documents and embeddings is not None:
            updated_metadatas = [
                {**(meta or {}), "crawl_period": "previous"}
                for meta in (data["metadatas"] or [{} for _ in documents])
            ]
            vs_previous._collection.add(
                ids=data["ids"],
                documents=documents,
                metadatas=updated_metadatas,
                embeddings=embeddings,
            )
            logger.info("[VDB] Promoted %d document(s) to previous", len(documents))

        self.delete_current()
        logger.info("[VDB] Current collection wiped")

    def delete_current(self) -> None:
        try:
            self._get_client().delete_collection(COLLECTION_CURRENT)
        except Exception:
            logger.debug("[VDB] Current collection did not exist, skipping delete")
        self._vs_current = None
        logger.info("[VDB] Current collection deleted")

    def delete_previous(self) -> None:
        try:
            self._get_client().delete_collection(COLLECTION_PREVIOUS)
        except Exception:
            logger.debug("[VDB] Previous collection did not exist, skipping delete")
        self._vs_previous = None
        logger.info("[VDB] Previous collection deleted")

    def store_documents(
        self,
        chunks: list[Document],
        ids: list[str]
    ) -> None:
        if not chunks:
            return
        vs = self._get_vectorstore()
        unique: list[Document] = []
        unique_ids: list[str] = []
        
        for chunk, chunk_id in zip(chunks, ids):
            unique.append(
                Document(
                    page_content=chunk.page_content,
                    metadata={**chunk.metadata, "crawl_period": "current"},
                )
            )
            unique_ids.append(chunk_id)
        
        if not unique:
            return
        
        vs.add_documents(documents=unique, ids=unique_ids)
        logger.info("[VDB] Stored %d/%d document(s)", len(unique), len(chunks))

    def search_all(self, query: str, k: int = 20) -> list[tuple[Document, float]]:
        results: list[tuple[Document, float]] = []
        results.extend(
            self._get_vectorstore().similarity_search_with_relevance_scores(query, k=k)
        )
        results.extend(
            self._get_previous_vectorstore().similarity_search_with_relevance_scores(query, k=k)
        )
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


_db = _VectorDB()

store_documents = _db.store_documents
search_all = _db.search_all
promote_current_to_previous = _db.promote_current_to_previous
delete_current = _db.delete_current
delete_previous = _db.delete_previous
