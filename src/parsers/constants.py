from pathlib import Path

from langchain_docling.loader import ExportType
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

from src.vector_database.constants import _EMBED_MODEL

_EMBED_MODEL_PATH = Path("./models/multilingual-e5-large")

if not _EMBED_MODEL_PATH.exists():
    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id=_EMBED_MODEL,
        local_dir=_EMBED_MODEL_PATH,
        ignore_patterns=[
            "pytorch_model.bin", "flax_model*", "tf_model*", "rust_model*",
            "*.msgpack", "onnx/*", "openvino/*", "*.yaml",
        ],
    )

_TOKENIZER = AutoTokenizer.from_pretrained(str(_EMBED_MODEL_PATH))
_EXPORT_TYPE = ExportType.DOC_CHUNKS
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
