from langchain_docling.loader import ExportType
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

from src.vector_database.constants import EMBED_MODEL

_TOKENIZER = AutoTokenizer.from_pretrained(EMBED_MODEL)
_EXPORT_TYPE = ExportType.DOC_CHUNKS
_CHUNKER = HybridChunker(
    tokenizer=HuggingFaceTokenizer(
        tokenizer=_TOKENIZER,
        max_tokens=512,
    ))
_SEPARATOR = "---NEXT_TABLE---"
_PRIMITIVES = (str, int, float, bool)
