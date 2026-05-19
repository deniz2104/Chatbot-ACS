import hashlib
import json
import logging
import torch
from pathlib import Path
from urllib.parse import urlparse

from datasketch import MinHash, MinHashLSH
from twisted.internet.threads import deferToThread

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from src.spider.items import DocumentItem
from src.spider.content_utils import normalize_url
from src.ai_prompts.keywords_extractor import extract_keywords
from src.parsers.entries import PageEntry, DocumentEntry
from src.parsers.content_parser.markdown_parser import process_markdown
from src.parsers.documents_parser.documents_orchestrator import parse_document
from src.spider.websites import Website
from src.categorization.matcher import categorize
from src.vector_database.vector_db import store_documents
from src.parsers.utils import sanitize_chunks
from src.categorization.load_encode import load_and_encode_categories

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

THRESHOLD = 0.75
NUM_PERM = 128

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

class KeywordExtractionPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if "text_content" not in adapter:
            return item

        text_content = adapter.get("text_content", "")
        
        def _extract():
            return extract_keywords(text_content)

        def _on_done(all_keywords):
            adapter["content"] = all_keywords
            del adapter["text_content"]
            return item

        def _on_error(failure):
            logger.error("[KEYWORDS] Extraction failed for %s: %s", adapter.get("url", "?"), failure.getErrorMessage())
            adapter["content"] = []
            if "text_content" in adapter:
                del adapter["text_content"]
            return item

        return deferToThread(_extract).addCallback(_on_done).addErrback(_on_error)


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
            try:
                store_documents(unique_text_chunks, ids=[c.metadata["content_hash"] for c in unique_text_chunks])
                logger.info("[CONTENT] Stored %d chunk(s)", len(unique_text_chunks))
            except Exception as e:
                logger.error("[CONTENT] Failed to store text chunks for %s: %s", adapter.get("url", "?"), e)

        if table_chunks:
            table_chunks = sanitize_chunks(table_chunks)
            try:
                store_documents(table_chunks, ids=[hashlib.sha256(c.page_content.encode()).hexdigest() for c in table_chunks])
                logger.info("[CONTENT] Stored %d table chunk(s)", len(table_chunks))
            except Exception as e:
                logger.error("[CONTENT] Failed to store table chunks for %s: %s", adapter.get("url", "?"), e)
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


class DocumentFilesPipeline(FilesPipeline):
    def item_completed(self, results, item, info):
        item = super().item_completed(results, item, info)

        if not isinstance(item, DocumentItem):
            return item

        adapter = ItemAdapter(item)
        files = adapter.get("files", [])
        if not files:
            return item

        chunks = parse_document(DocumentEntry(
            url_slug=adapter.get("document_url", ""),
            title=adapter.get("document_url_text", ""),
            local_path=files[0]["path"],
        ))
        if chunks:
            chunks = sanitize_chunks(chunks)
            try:
                store_documents(chunks, ids=[hashlib.sha256(c.page_content.encode()).hexdigest() for c in chunks])
                logger.info("[DOCS] Stored %d chunk(s) from %s", len(chunks), files[0]["path"])
            except Exception as e:
                logger.error("[DOCS] Failed to store chunks from %s: %s", files[0]["path"], e)

        return item

class GeneralOutputPipeline:
    def __init__(self):
        self.general_entries: dict[str, dict[str, dict]] = {}
    
    def open_spider(self, spider):
        self._output_dir = Path(spider.settings["FILES_STORE"])
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._website_map: dict[str, Website] = {urlparse(w.url).hostname: w for w in spider.websites}
        self._website_keywords: dict[str, dict[str, list[str]]] = {
            hostname: website.keywords for hostname, website in self._website_map.items()
        }

    def _build_general_entry(self, url: str, domain: str, title: str, keywords: list[str]) -> dict:
        return {"url": url, "domain": domain, "title": title, "keywords": keywords}

    def process_item(self, item, _spider):
        adapter = ItemAdapter(item)
        url = adapter.get("url", "")
        domain = urlparse(url).hostname
        title = adapter.get("url_text", "")

        website = self._website_map.get(domain)
        if not website:
            logger.debug("[OUTPUT] No website config for domain %s, skipping", domain)
            return item

        page_keywords = adapter.get("content") or []
        category = categorize(page_keywords, self._website_keywords[domain])
        if category is None:
            logger.debug("[OUTPUT] No category matched for %s", url)
            return item

        entry = self._build_general_entry(url, domain, title, page_keywords)
        domain_data = self.general_entries.setdefault(domain, {})
        domain_data.setdefault(category, {
            "predefined_keywords": website.keywords.get(category, []),
            "urls": [],
        })["urls"].append(entry)
        return item

    def close_spider(self, spider):
        path = self._output_dir / "general_output.json"
        path.write_text(json.dumps(self.general_entries, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[OUTPUT] Wrote output to %s", path)

        categories = load_and_encode_categories(self.general_entries)
        torch.save(categories, self._output_dir / "categories_encoded.pt")
        logger.info("[OUTPUT] Pre-encoded %d categories to categories_encoded.pt", len(categories))
        del self.general_entries

class ChatbotOutputPipeline:
    def __init__(self):
        self.chatbot_entries: set[str] = set()

    def open_spider(self, spider):
        self._output_dir = Path(spider.settings["FILES_STORE"])
        self._output_dir.mkdir(parents=True, exist_ok=True)
        path = self._output_dir / "chatbot_output.json"
        try:
            self.chatbot_entries = set(json.loads(path.read_text(encoding="utf-8")))
            logger.info("[OUTPUT] Loaded %d existing chatbot entries", len(self.chatbot_entries))
        except (FileNotFoundError, json.JSONDecodeError):
            self.chatbot_entries = set()
        logger.info("[OUTPUT] Writing JSON output to: %s", self._output_dir)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        is_doc = isinstance(item, DocumentItem)

        url_field = "document_url" if is_doc else "url"
        self.chatbot_entries.add(adapter.get(url_field, ""))

        return item

    def close_spider(self, spider):
        path = self._output_dir / "chatbot_output.json"
        path.write_text(json.dumps(list(self.chatbot_entries), ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("[OUTPUT] Wrote output to %s", path)
        del self.chatbot_entries
