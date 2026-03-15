import redis
import scrapy
import trafilatura

from src.spider.constants import REDIS_KEYS
from w3lib.url import canonicalize_url

def normalize_url(url: str) -> str:
    canon = canonicalize_url(url)
    if not canon:
        return canon
    if canon.startswith("http://"):
        canon = "https://" + canon[7:]
    canon = canon.replace("://www.", "://", 1)
    return canon

def flush_redis(redis_url: str) -> None:
    try:
        r = redis.from_url(redis_url)
        for key in REDIS_KEYS:
            if r.delete(key):
                print(f"Flushed Redis key '{key}'")
        r.close()
    except redis.ConnectionError:
        print(f"Could not connect to Redis at {redis_url} — skipping flush")
    except redis.RedisError as e:
        print(f"Redis error during flush: {e}")

def extract_content(response: scrapy.http.Response) -> str:
    return trafilatura.extract(response.text, include_comments=False, include_tables=False) or ""