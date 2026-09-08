import re
from hashlib import sha256
from urllib.parse import urlparse

from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response, HtmlResponse
from scrapy.loader import ItemLoader
from scrapy.linkextractors import LinkExtractor
from itemloaders.processors import TakeFirst
from flowmark import reformat_text

from src.spider.items import DocumentItem, PageItem
from src.spider.link_utils import DOCUMENT_EXTENSIONS, DENY_PATTERNS
from src.spider.content_utils import normalize
from src.parsers.html_to_markdown.content_parser import parse_content
from src.parsers.html_to_markdown.table_parser import (
    select_tables_from_plain_html,
    tables_to_markdown,
)
from src.parsers.constants import _SEPARATOR

class ItemLoaderCustom(ItemLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_output_processor = TakeFirst()

class PageSpider(CrawlSpider):
    name = "link_website_crawler"
    start_urls: list[str] = []
    allowed_domains: list[str] = []

    def __init__(
        self, *args, start_urls: list[str]):
        self.start_urls = start_urls
        self.allowed_domains = [h for url in self.start_urls if (h := urlparse(url).hostname)]
        self.exact_domain_allow = re.compile(
            "|".join(rf"https?://{re.escape(d)}(/|$)" for d in self.allowed_domains)
        )
        deny_regex = re.compile("|".join(DENY_PATTERNS))

        self.rules = (
            Rule(
                LinkExtractor(
                    allow=self.exact_domain_allow,
                    deny=deny_regex,
                    canonicalize=True,
                ),
                callback="parse_page",
                follow=True
            ),
        )
        super().__init__(*args)

    def _extract_headings(self, response: HtmlResponse) -> str:
        heading_lines : list[str] = []

        for tag, prefix in [("h1", "#"), ("h2", "##"), ("h3", "###")]:
            for text in response.css(f"{tag}::text").getall():
                text = normalize(text) if text else ""
                heading_lines.append(f"{prefix} {text}")
        
        heading_block = "\n".join(heading_lines)

        return heading_block

    def parse_page(self, response: Response):
        if not isinstance(response, HtmlResponse):
            self.logger.debug("[SKIP] Non-HTML response: %s", response.url)
            return

        raw_markdown = parse_content(response)
        if not raw_markdown:
            self.logger.warning("[NO_CONTENT] %s", response.url)
            return

        markdown_content = reformat_text(raw_markdown, smartquotes=True, ellipses=True)
        
        loader = ItemLoaderCustom(item=PageItem())

        tables = tables_to_markdown(select_tables_from_plain_html(response))
        content_hash = sha256(markdown_content.encode("utf-8")).hexdigest()

        heading_block = self._extract_headings(response)
        markdown_content = f"{heading_block}\n\n{markdown_content}" if heading_block else markdown_content

        page_title = (
            response.css("title::text").get("").strip()
            or " ".join(response.css("h1::text").extract()).strip()
            or response.meta.get("link_text", "")
        )
        loader.add_value("url_text", page_title)
        loader.add_value("url", response.url)
        loader.add_value("content", markdown_content)
        loader.add_value("tables", _SEPARATOR.join(tables))
        loader.add_value("hash", content_hash)

        yield loader.load_item()

        yield from self._extract_documents(response)
        self.logger.info("[CRAWLED] %s", response.url)

    def _extract_documents(self, response: Response):
        for anchor in response.css("a, area"):
            url = anchor.attrib.get("href")
            if not url:
                continue

            full_url = response.urljoin(url)
            is_document = re.search(DOCUMENT_EXTENSIONS, full_url, re.IGNORECASE)
            has_download_attr = anchor.attrib.get("download") is not None
            if not (is_document or has_download_attr):
                continue

            link_text = (
                normalize(" ".join(anchor.css("::text").getall()))
                or normalize(anchor.attrib.get("title", ""))
            )
            document_hash = sha256(full_url.encode("utf-8")).hexdigest()

            loader = ItemLoaderCustom(item=DocumentItem())
            loader.add_value("document_url_text", link_text)
            loader.add_value("document_url", full_url)
            loader.add_value("document_hash", document_hash)
            item = loader.load_item()
            item["file_urls"] = [full_url]
            yield item
            self.logger.info("[DOCUMENT] %s", full_url)