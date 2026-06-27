import logging
import math

from src.azure.db.table_client import get_url_hotspots_table_client

logger = logging.getLogger(__name__)

_TOP_FRACTION = 0.20


def get_hotspot_filter(connection_string: str) -> list[str] | None:
    try:
        client = get_url_hotspots_table_client(connection_string)
        entities = list(client.list_entities())
        if not entities:
            return None

        by_domain: dict[str, list[tuple[str, int]]] = {}
        for entity in entities:
            url = entity.get("url", "")
            domain = entity["PartitionKey"]
            count = entity.get("count", 0)
            if url:
                by_domain.setdefault(domain, []).append((url, count))

        result: list[str] = []
        for domain, urls in by_domain.items():
            urls.sort(key=lambda x: -x[1])
            top_n = max(math.ceil(len(urls) * _TOP_FRACTION), 1)
            result.extend(url for url, _ in urls[:top_n])
            logger.debug("[HOTSPOT] %s: %d/%d URLs in filter", domain, top_n, len(urls))

        logger.debug("[HOTSPOT] Filter: %d URL(s) across %d domain(s)", len(result), len(by_domain))
        return result or None
    except Exception as e:
        logger.warning("[HOTSPOT] get_hotspot_filter failed: %s", e)
        return None
