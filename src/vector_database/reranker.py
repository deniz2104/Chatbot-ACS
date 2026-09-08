import logging
from sentence_transformers import CrossEncoder
from pathlib import Path

_RERANKER_PATH = "./models/bge-reranker-v2-m3"

logger = logging.getLogger(__name__)

class Reranker():
    _reranker = None

    @classmethod
    def get_reranker(cls) -> CrossEncoder:
        if cls._reranker is None:
            if not Path(_RERANKER_PATH).exists():
                raise FileNotFoundError(f"Reranker model not found at {_RERANKER_PATH}")
            
            model = str(_RERANKER_PATH)
            cls._reranker = CrossEncoder(model, max_length=512)
            logger.info("[VDB] Reranker loaded from: %s", model)
            
        return cls._reranker

    def __init__(self):
        self.get_reranker()