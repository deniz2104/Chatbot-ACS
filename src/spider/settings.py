from src.azure.kv.get_secrets_from_kv import get_redis_url, get_file_store

BOT_NAME = "acs_spider"

SPIDER_MODULES = ["src.spider.crawler"]

ROBOTSTXT_OBEY = True

REDIS_URL = get_redis_url()

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "src.spider.link_duplicates.NormalizedDupeFilter"
SCHEDULER_PERSIST = False

CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 32
DOWNLOAD_DELAY = 0

COOKIES_ENABLED = True

ITEM_PIPELINES = {
    "src.spider.pipelines.ValidationPipeline": 100,
    "src.spider.pipelines.DeduplicationPipeline": 200,
    "src.spider.pipelines.DocumentFilesPipeline": 300,
    "src.spider.pipelines.ContentChunkingPipeline": 400,
}

DOWNLOADER_MIDDLEWARES = {
    "src.spider.middlewares.RotatingHeadersMiddleware": 400,
}

LOG_LEVEL = "INFO"

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500,502,503,504,408,421,429]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.25
AUTOTHROTTLE_MAX_DELAY = 3.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0

DEPTH_LIMIT = 25

CLOSESPIDER_TIMEOUT = 0
CLOSESPIDER_ERRORCOUNT = 20

DNS_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 15

REACTOR_THREADPOOL_MAXSIZE = 20
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 500

DOWNLOADER_CLIENTCONTEXTFACTORY = "src.spider.ssl_context.CustomContextFactory"

FILES_STORE = get_file_store()