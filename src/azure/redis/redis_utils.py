import logging
import redis

from contextlib import contextmanager

logger = logging.getLogger(__name__)

REDIS_KEYS: tuple = (
    "link_website_crawler:dupefilter",
    "link_website_crawler:requests",
)

@contextmanager
def _redis_session(redis_url: str, operation: str):
    r: redis.Redis | None = None
    try:
        r = redis.Redis.from_url(redis_url)
        r.ping() 
        logger.debug("[REDIS] Connected to %s", redis_url)
    except (redis.ConnectionError, redis.TimeoutError):
        logger.warning("[REDIS] Could not connect to %s — skipping %s", redis_url, operation)
        r = None
    except redis.RedisError as e:
        logger.error("[REDIS] Error connecting for %s: %s", operation, e)
        r = None
    try:
        yield r
    except redis.RedisError as e:
        logger.error("[REDIS] Error during %s: %s", operation, e)
    finally:
        if r is not None:
            r.close()

def flush_redis(redis_url: str) -> None:
    with _redis_session(redis_url, "flush") as r:
        if r is None:
            return
        for key in REDIS_KEYS:
            if r.delete(key):
                logger.info("[REDIS] Flushed key '%s'", key)
