import logging

from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess

from src.spider.crawler.page_spider import PageSpider
from src.spider.redis_utils import flush_redis

logger = logging.getLogger(__name__)


class SpiderRunner:
    def __init__(
        self, main_settings: str = "src.spider.settings") -> None:
        self._settings = Settings()
        self._settings.setmodule(main_settings, priority="project")

    def run(self, urls: list[str]) -> None:
        if self._settings.get("REDIS_URL"):
            flush_redis(redis_url=self._settings["REDIS_URL"])

        logger.info("Starting crawler for %d URL(s): %s", len(urls), urls)
        process = CrawlerProcess(self._settings)
        process.crawl(PageSpider, start_urls=urls)
        process.start()
        logger.info("Crawler process finished")

    def crawl(self, urls: list[str]) -> None:
        self.run(urls)
