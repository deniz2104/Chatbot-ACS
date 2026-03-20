import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.spider.crawler.page_spider import PageSpider, SitemapPageSpider
from src.spider.utils import flush_redis
from src.spider.utils import get_urls

def main() -> None:
    os.environ["SCRAPY_SETTINGS_MODULE"] = "src.spider.settings"
    settings = get_project_settings()

    flush_redis(settings.get("REDIS_URL"))

    crawl_urls = get_urls(has_sitemap=False)
    sitemap_urls = get_urls(has_sitemap=True)

    process = CrawlerProcess(settings)

    if crawl_urls:
        process.crawl(PageSpider, website_urls=crawl_urls)
    if sitemap_urls:
        process.crawl(SitemapPageSpider, website_urls=sitemap_urls)

    process.start()

if __name__ == "__main__":
    main()
