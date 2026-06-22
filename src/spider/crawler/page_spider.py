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

class PageSpider(CrawlSpider):
    name = "link_website_crawler"
    start_urls: list[str] = []
    allowed_domains: list[str] = []

    def __init__(
        self, *args, start_urls: list[str]):
        self.start_urls = start_urls
        self.allowed_domains = [h for url in self.start_urls if (h := urlparse(url).hostname)]
        self.default_processor = TakeFirst()
    
        min_year = datetime.now().year - 2
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
        super().__init__(*args)

    def parse_page(self, response: Response):
        if not isinstance(response, HtmlResponse):
            self.logger.debug("[SKIP] Non-HTML response: %s", response.url)
            return

        text_content = normalize(parse_content(response, output_format="txt"))
        if not text_content:
            self.logger.warning(f"[NO_CONTENT] {response.url}")
            return
        
        loader = ItemLoader(item=PageItem(), response=response)
        loader.default_output_processor = self.default_processor

        tables = tables_to_markdown(select_tables_from_plain_html(response))
        content_hash = sha256(text_content.encode("utf-8")).hexdigest()
        raw_markdown = normalize_markdown(parse_content(response))

        # Inject heading structure from HTML before Docling sees the content.
        # Trafilatura strips <h> tags, so Docling would never see them otherwise.
        heading_lines = []
        for tag, prefix in [("h1", "#"), ("h2", "##"), ("h3", "###")]:
            for text in response.css(f"{tag}::text").getall():
                text = text.strip()
                if text:
                    heading_lines.append(f"{prefix} {text}")
        heading_block = "\n".join(heading_lines)
        markdown_content = f"{heading_block}\n\n{raw_markdown}" if heading_block else raw_markdown

        page_title = (
            response.css("title::text").get("").strip()
            or response.css("h1::text").get("").strip()
            or response.meta.get("link_text", "")
        )
        loader.add_value("url_text", page_title)
        loader.add_value("url", response.url)
        loader.add_value("content", markdown_content)
        loader.add_value("tables", _SEPARATOR.join(tables))
        loader.add_value("hash", content_hash)

        yield loader.load_item()

        yield from self._extract_documents(response)
        self.logger.info(f"[CRAWLED] {response.url}")

    def _extract_documents(self, response: Response):
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

