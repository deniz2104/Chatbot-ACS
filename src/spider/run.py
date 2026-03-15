import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.spider.crawler.crawl_links_from_single_website import PageSpider
from src.spider.utils import flush_redis

WEBSITES = [
    "https://acs.pub.ro",
]

def main() -> None:
    os.environ["SCRAPY_SETTINGS_MODULE"] = "src.spider.settings"
    settings = get_project_settings()

    flush_redis(settings.get("REDIS_URL"))

    process = CrawlerProcess(settings)
    for url in WEBSITES:
        process.crawl(PageSpider, website_url=url)
    process.start()

if __name__ == "__main__":
    main()
