import redis as _redis
from src.azure.kv.get_secrets_from_kv import get_redis_url, get_file_store

BOT_NAME = "acs_spider"

SPIDER_MODULES = ["src.spider.crawler"]

ROBOTSTXT_OBEY = True


def _redis_reachable(url: str) -> bool:
    try:
        r = _redis.Redis.from_url(url, socket_connect_timeout=2)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


_raw_redis_url = get_redis_url()
REDIS_URL = _raw_redis_url if (_raw_redis_url and _redis_reachable(_raw_redis_url)) else None

if REDIS_URL:
    SCHEDULER = "scrapy_redis.scheduler.Scheduler"
    DUPEFILTER_CLASS = "src.spider.link_duplicates.NormalizedDupeFilter"
    SCHEDULER_PERSIST = False
else:
    SCHEDULER = "scrapy.core.scheduler.Scheduler"
    DUPEFILTER_CLASS = "scrapy.dupefilters.RFPDupeFilter"

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