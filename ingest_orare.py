#!/usr/bin/env python3
"""
Ingests XLS schedule files from the Desktop into the actual ChromaDB.
Maps each file to its canonical web URL from acs.pub.ro/educatie/orare/.
Safe to re-run: uses upsert semantics, never deletes anything.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path

os.environ["CHROMA_LOCAL_PATH"] = "./chroma_db"
sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("anthropic").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

from src.parsers.documents_parser.documents_orchestrator import parse_document
from src.parsers.entries import DocumentEntry
from src.parsers.utils import sanitize_chunks
from src.spider.content_utils import normalize_url
from src.vector_database.vector_db import store_documents, get_all_url_chunk_ids

_DESKTOP = Path.home() / "Desktop"
_BASE_URL = "https://acs.pub.ro/~cpop/orare_sem2"


def _slug(filename: str) -> str:
    return normalize_url(f"{_BASE_URL}/{filename}")


def main() -> None:
    files = sorted(_DESKTOP.glob("*.xls")) + sorted(_DESKTOP.glob("*.xlsx"))
    if not files:
        print("No XLS/XLSX files found on Desktop.")
        sys.exit(0)

    print(f"Found {len(files)} file(s) on Desktop.")
    print("Checking existing chunks in ChromaDB...")
    existing = get_all_url_chunk_ids()
    print(f"ChromaDB currently has {sum(len(v) for v in existing.values())} chunks across {len(existing)} URL slugs.\n")

    total_added = 0
    total_skipped = 0

    for path in files:
        slug = _slug(path.name)
        already = existing.get(slug, set())

        if already:
            print(f"[SKIP]  {path.name}  →  {len(already)} chunk(s) already in DB")
            total_skipped += 1
            continue

        print(f"[INGEST] {path.name}  →  {slug}")
        entry = DocumentEntry(
            url_slug=slug,
            title=path.stem,
            local_path=str(path),
        )

        chunks = parse_document(entry)
        if not chunks:
            print(f"         No chunks produced — skipping.")
            continue

        chunks = sanitize_chunks(chunks)
        ids = [hashlib.sha256(c.page_content.encode()).hexdigest() for c in chunks]
        store_documents(chunks, ids)
        print(f"         Stored {len(chunks)} chunk(s).")
        total_added += 1

    print(f"\nDone. Ingested: {total_added} file(s), skipped (already in DB): {total_skipped} file(s).")


if __name__ == "__main__":
    main()
