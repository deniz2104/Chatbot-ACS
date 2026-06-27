import hashlib
import logging
import shutil
from pathlib import Path

from datasketch import MinHash, MinHashLSH

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from src.spider.items import DocumentItem
from src.spider.content_utils import normalize_url
from src.parsers.entries import PageEntry, DocumentEntry
from src.parsers.content_parser.markdown_parser import process_markdown
from src.parsers.documents_parser.documents_orchestrator import parse_document
from src.vector_database.vector_db import store_documents
from src.parsers.utils import sanitize_chunks
from src.spider.constants import THRESHOLD, NUM_PERM
from src.spider.error_handlers import pipeline_error

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class ValidationPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        url = adapter.get("url") or adapter.get("document_url")
        if not url:
            logger.debug("[VALIDATION] Dropping item — missing url")
            raise DropItem("Missing url")
        url_field = "document_url" if "document_url" in adapter else "url"
        adapter[url_field] = normalize_url(url)
        return item

class DeduplicationPipeline:
    def __init__(self):
        self.seen_urls: set[str] = set()
        self.seen_hashes: set[str] = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get("url") or adapter.get("document_url")
        if not url:
            raise DropItem("Missing url")
        if url in self.seen_urls:
            logger.debug("[DEDUP] Duplicate URL: %s", url)
            raise DropItem(f"Duplicate link: {url}")

        self.seen_urls.add(url)

        content_hash = adapter.get("hash")
        if content_hash:
            if content_hash in self.seen_hashes:
                logger.debug("[DEDUP] Duplicate content hash for: %s", url)
                raise DropItem(f"Duplicate content: {url}")
            self.seen_hashes.add(content_hash)

        return item
    
    def close_spider(self, spider):
        del self.seen_urls
        del self.seen_hashes

class DocumentFilesPipeline(FilesPipeline):
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = super().from_crawler(crawler)
        pipeline._files_store_path = Path(crawler.settings.get("FILES_STORE", "/tmp/scrapy_files"))
        return pipeline

    def close_spider(self, spider):
        if self._files_store_path.exists():
            shutil.rmtree(self._files_store_path)
            logger.info("[CLEANUP] Deleted files store: %s", self._files_store_path)

    def get_media_requests(self, item, info):
        for request in super().get_media_requests(item, info):
            yield request.replace(meta={**request.meta, "download_timeout": 200})

    def item_completed(self, results, item, info):
        item = super().item_completed(results, item, info)

        if not isinstance(item, DocumentItem):
            return item

        adapter = ItemAdapter(item)
        files = adapter.get("files", [])
        if not files:
            return item

        chunks = []
        with pipeline_error("DOCS", files[0]["path"]):
            chunks = parse_document(DocumentEntry(
                url_slug=adapter.get("document_url", ""),
                title=adapter.get("document_url_text", ""),
                local_path=str(self.store._get_filesystem_path(files[0]["path"])),
            ))

        if chunks:
            chunks = sanitize_chunks(chunks)
            id_to_chunk = {hashlib.sha256(c.page_content.encode()).hexdigest(): c for c in chunks}
            with pipeline_error("DOCS", files[0]["path"]):
                store_documents(list(id_to_chunk.values()), ids=list(id_to_chunk.keys()))
                logger.info("[DOCS] Stored %d chunk(s) from %s", len(id_to_chunk), files[0]["path"])

        return item
    
class ContentChunkingPipeline:
    def open_spider(self, spider):
        self.seen_content: set[str] = set()
        self._lsh = MinHashLSH(threshold=THRESHOLD, num_perm=NUM_PERM)
        self._lsh_count = 0

    def process_item(self, item, spider):
        if isinstance(item, DocumentItem):
            return item

        adapter = ItemAdapter(item)
        text_chunks, table_chunks = process_markdown(PageEntry(
            url_slug=adapter.get("url", ""),
            title=adapter.get("url_text", ""),
            text=adapter.get("content", ""),
            tables=adapter.get("tables", ""),
        ))
        unique_text_chunks = self._dedup(text_chunks)
        if unique_text_chunks:
            unique_text_chunks = sanitize_chunks(unique_text_chunks)
            id_to_text = {c.metadata["content_hash"]: c for c in unique_text_chunks}
            with pipeline_error("CONTENT", adapter.get("url", "?")):
                store_documents(list(id_to_text.values()), ids=list(id_to_text.keys()))
                logger.info("[CONTENT] Stored %d chunk(s)", len(id_to_text))

        if table_chunks:
            table_chunks = sanitize_chunks(table_chunks)
            id_to_table = {hashlib.sha256(c.page_content.encode()).hexdigest(): c for c in table_chunks}
            with pipeline_error("CONTENT", adapter.get("url", "?")):
                store_documents(list(id_to_table.values()), ids=list(id_to_table.keys()))
                logger.info("[CONTENT] Stored %d table chunk(s)", len(id_to_table))
        return item

    def _make_minhash(self, text: str) -> MinHash:
        m = MinHash(num_perm=NUM_PERM)
        for shingle in {text[i:i + 5] for i in range(len(text) - 4)}:
            m.update(shingle.encode())
        return m

    def _dedup(self, chunks: list[Document]) -> list[Document]:
        result = []
        for chunk in chunks:
            h = hashlib.sha256(chunk.page_content.encode()).hexdigest()
            chunk.metadata["content_hash"] = h

            if h in self.seen_content:
                continue

            mh = self._make_minhash(chunk.page_content)
            if self._lsh.query(mh):
                logger.info("[DEDUP] Near-dup (MinHash) skipped chunk")
                continue

            key = f"c{self._lsh_count}"
            self._lsh.insert(key, mh)
            self._lsh_count += 1
            self.seen_content.add(h)
            result.append(chunk)

        return result
    
    def close_spider(self, spider):
        del self.seen_content
        del self._lsh
        del self._lsh_count