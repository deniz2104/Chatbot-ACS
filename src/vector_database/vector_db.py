import logging

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from chromadb.api.collection_configuration import (
    CreateCollectionConfiguration,
    CreateHNSWConfiguration,
)
from langchain_core.documents import Document

from src.vector_database.constants import _CHUNKS_CHOSEN, _SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

_EMBED_MODEL_PATH = "./models/multilingual-e5-large"
COLLECTION_NAME = "Chatbot ACS"

class VectorDatabase:
    _config: CreateCollectionConfiguration = {
        "hnsw": CreateHNSWConfiguration(
            space="cosine",
            ef_search=50,
            ef_construction=100,
            max_neighbors=12,
        )
    }
    _client = None
    _embeddings: embedding_functions.SentenceTransformerEmbeddingFunction | None = None
    _collection = None
    _documents : list[Document] = []

    def __init__(self):
            self._raw_collection = self.get_collection().get(include=["documents", "metadatas", "distances"])

    @staticmethod
    def make_embedding_function():
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=str(_EMBED_MODEL_PATH),
            normalize_embeddings=True,
        )
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
                ))
        return cls._client

    @classmethod
    def get_embeddings(cls):
        if cls._embeddings is None:
            cls._embeddings = cls.make_embedding_function()
        return cls._embeddings

    @classmethod
    def get_collection(cls):
        if cls._collection is None:
            cls._collection = cls.get_client().get_or_create_collection(
                COLLECTION_NAME,
                configuration=cls._config,
                embedding_function=cls.get_embeddings()  # type: ignore[arg-type]
            )
        return cls._collection

    @classmethod
    def get_documents(cls) -> list[Document]:
        if not cls._documents:
            raw = cls.get_collection().get()

        return [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(raw["documents"], raw["metadatas"])
        ]

    @classmethod
    def reset_collection(cls):
        cls.get_client().delete_collection(COLLECTION_NAME)
        cls._collection = None
        cls._documents = []
        logger.info("[VDB] Collection reset")

    def store_documents(self, chunks: list[Document], ids: list[str]) -> None:
        self.get_collection().add(
            ids=ids,
            documents=[chunk.page_content for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
        )
        logger.info("[VDB] Stored %d document(s)", len(chunks))

    def search_by_vector(
        self, embedding: list[float], k: int = _CHUNKS_CHOSEN, urls: set[str] | None = None
    ) -> list[Document]:
        url_hotspot_filter = {"url_slug": {"$in": urls}} if urls else None
        result = self.get_collection().query(
            query_embeddings=[embedding],
            n_results=k,
            where=url_hotspot_filter,
            include=["documents", "metadatas", "distances"],
        )

        return [Document(page_content=doc, metadata=meta) for doc, meta, dist in zip(
                result["documents"][0], result["metadatas"][0], result["distances"][0] 
            )
            if 1 - dist >= _SIMILARITY_THRESHOLD
        ]