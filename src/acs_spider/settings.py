BOT_NAME = "acs_spider"

FEEDS = {"src/acs_spider/output.jsonl": {"format": "jsonlines", "encoding": "utf-8", "overwrite": True}}

SPIDER_MODULES = ["src.acs_spider.spiders"]
NEWSPIDER_MODULE = "src.acs_spider.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 16

DOWNLOAD_DELAY = 1

COOKIES_ENABLED = False

DOWNLOADER_MIDDLEWARES = {
    "src.acs_spider.middlewares.RotatingHeadersMiddleware": 400,
}

LOG_LEVEL = "WARNING"

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

DOWNLOADER_CLIENTCONTEXTFACTORY = "src.acs_spider.ssl_context.CustomContextFactory"
