import os
import re
from datetime import datetime
from hashlib import sha256
from urllib.parse import urlparse

from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response, HtmlResponse
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from itemloaders.processors import TakeFirst

from src.spider.items import DocumentItem, PageItem
from src.spider.link_utils import DOCUMENT_EXTENSIONS, DENY_PATTERNS, build_year_deny_pattern
from src.spider.content_utils import normalize, normalize_markdown
from src.parsers.html_to_markdown.content_parser import parse_content
from src.parsers.html_to_markdown.table_parser import (
    select_tables_from_plain_html,
    tables_to_markdown,
)
from src.parsers.constants import _SEPARATOR
from src.crawl_settings.constants import CHATBOT_SETTINGS

class PageSpider(CrawlSpider):
    name = "link_website_crawler"
    start_urls: list[str] = []
    allowed_domains: list[str] = []

    def __init__(
        self, *args, start_urls: list[str], has_docs: bool = False, websites=None, **kwargs):
        self.start_urls = start_urls
        self.allowed_domains = [h for url in self.start_urls if (h := urlparse(url).hostname)]
        self.default_processor = TakeFirst()
        self.has_docs = has_docs
        self.websites = websites or []
        self.chatbot_settings : bool = self.settings.get("SETTINGS_MODULE") == CHATBOT_SETTINGS

        min_year = datetime.now().year - int(os.environ.get("YEAR_LOOKBACK", "2"))
        deny_regex = re.compile("|".join(DENY_PATTERNS))
        year_deny_regex = re.compile(rf"(?<!\d)({build_year_deny_pattern(min_year)})(?!\d)")

        self.exact_domain_allow = re.compile(
            "|".join(rf"https?://{re.escape(d)}(/|$)" for d in self.allowed_domains)
        )

        self.rules = (
            Rule(
                LinkExtractor(
                    allow=self.exact_domain_allow,
                    deny=(deny_regex, year_deny_regex, DOCUMENT_EXTENSIONS),
                    unique=True,
                    canonicalize=True,
                ),
                callback="parse_page",
                follow=True,
            ),
        )
        super().__init__(*args, **kwargs)

    def parse_page(self, response: Response):
        if not isinstance(response, HtmlResponse):
            self.logger.debug("[SKIP] Non-HTML response: %s", response.url)
            return

        text_content = normalize(parse_content(response, output_format="txt"))
        if not text_content:
            self.logger.warning(f"[NO_CONTENT] {response.url}")
            return

        content_hash = sha256(text_content.encode("utf-8")).hexdigest()

        if self.chatbot_settings:
            markdown_content = normalize_markdown(parse_content(response))
            yield from self._yield_chatbot_item(response, markdown_content, content_hash)
        else:
            yield from self._yield_general_item(response, text_content, content_hash)

        yield from self._extract_documents(response)
        self.logger.info(f"[CRAWLED] {response.url}")

    def _yield_chatbot_item(self, response: HtmlResponse, markdown_content: str, content_hash: str):
        tables = tables_to_markdown(select_tables_from_plain_html(response))
        loader = ItemLoader(item=PageItem(), response=response)
        loader.default_output_processor = self.default_processor
        loader.add_value("url_text", response.meta.get("link_text", ""))
        loader.add_value("url", response.url)
        loader.add_value("content", markdown_content)
        loader.add_value("tables", _SEPARATOR.join(tables))
        loader.add_value("hash", content_hash)
        yield loader.load_item()

    def _yield_general_item(self, response: HtmlResponse, text_content: str, content_hash: str):
        loader = ItemLoader(item=PageItem(), response=response)
        loader.default_output_processor = self.default_processor
        loader.add_value("url_text", response.meta.get("link_text", ""))
        loader.add_value("url", response.url)
        loader.add_value("text_content", text_content)
        loader.add_value("hash", content_hash)
        yield loader.load_item()

    def _extract_documents(self, response: Response):
        if not self.has_docs:
            return

        for anchor in response.css("a, area"):
            url = anchor.attrib.get("href")
            if not url:
                continue

            full_url = response.urljoin(url)
            if not re.search(DOCUMENT_EXTENSIONS, full_url, re.IGNORECASE):
                continue

            if not self.exact_domain_allow.match(full_url):
                continue

            link_text = "".join(anchor.css("::text").getall())
            loader = ItemLoader(item=DocumentItem())
            loader.default_output_processor = self.default_processor
            loader.add_value("document_url_text", link_text)
            loader.add_value("document_url", full_url)
            item = loader.load_item()
            item["file_urls"] = [full_url]
            yield item
            self.logger.info(f"[DOCUMENT] {full_url}")
