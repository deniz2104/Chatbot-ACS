import logging

from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess

from src.spider.crawler.page_spider import PageSpider
from src.azure.redis.redis_utils import flush_redis
from src.spider.constants import urls

logger = logging.getLogger(__name__)


class SpiderRunner:
    def __init__(
        self, main_settings: str = "src.spider.settings") -> None:
        self._settings = Settings()
        self._settings.setmodule(main_settings, priority="project")

    def run(self, start_urls: list[str]) -> None:
        if self._settings.get("REDIS_URL"):
            flush_redis(redis_url=self._settings["REDIS_URL"])

        logger.info("Starting crawler for %d URL(s): %s", len(start_urls), start_urls)
        process = CrawlerProcess(self._settings)
        process.crawl(PageSpider, start_urls=start_urls)
        process.start()
        logger.info("Crawler process finished")

    def crawl(self, start_urls: list[str] = urls) -> None:
        self.run(start_urls)

if __name__ == "__main__":
    runner = SpiderRunner()
    runner.crawl()
