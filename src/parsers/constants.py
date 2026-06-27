import os
from pathlib import Path

from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

_EMBED_MODEL_PATH = Path(os.environ.get("EMBED_MODEL_PATH", "./models/multilingual-e5-large"))

_TOKENIZER = AutoTokenizer.from_pretrained(str(_EMBED_MODEL_PATH))
_CHUNKER = HybridChunker(
    tokenizer=HuggingFaceTokenizer(
        tokenizer=_TOKENIZER,
        max_tokens=512,
    ))
_SEPARATOR = "---NEXT_TABLE---"
_PRIMITIVES = (str, int, float, bool)

_HEADER_SPLITTER = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "sheet")],
    strip_headers=False,
)

_TOKEN_SPLITTER = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    tokenizer=_TOKENIZER,
    chunk_size=512,
    chunk_overlap=32,
)

_DOCLING_INTERNAL_KEYS = {"doc_items", "origin", "schema_name", "version"}
