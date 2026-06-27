import logging
import math

from azure.data.tables import TableServiceClient

from src.azure.db.table_client import TABLE_URL_HOTSPOTS
from src.azure.kv.get_secrets_from_kv import get_storage_account_secret

logger = logging.getLogger(__name__)

_MIN_COUNT = 3
_MIN_TOTAL_URLS = 5
_TOP_FRACTION = 0.20


def get_hotspot_filter() -> list[str] | None:
    try:
        conn = get_storage_account_secret()
        client = TableServiceClient.from_connection_string(conn).get_table_client(TABLE_URL_HOTSPOTS)

        entities = list(client.list_entities())
        if not entities:
            return None

        by_domain: dict[str, list[tuple[str, int]]] = {}
        for entity in entities:
            count = entity.get("count", 0)
            if count < _MIN_COUNT:
                continue
            url = entity.get("url", "")
            domain = entity["PartitionKey"]
            if url:
                by_domain.setdefault(domain, []).append((url, count))

        result: list[str] = []
        for domain, urls in by_domain.items():
            urls.sort(key=lambda x: -x[1])
            top_n = max(math.ceil(len(urls) * _TOP_FRACTION), 1)
            result.extend(url for url, _ in urls[:top_n])
            logger.debug("[HOTSPOT] %s: %d/%d URLs in filter", domain, top_n, len(urls))

        if len(result) < _MIN_TOTAL_URLS:
            logger.debug("[HOTSPOT] Only %d URL(s) qualify — skipping filter", len(result))
            return None

        logger.debug("[HOTSPOT] Filter: %d URL(s) across %d domain(s)", len(result), len(by_domain))
        return result
    except Exception as e:
        logger.warning("[HOTSPOT] get_hotspot_filter failed: %s", e)
        return None
