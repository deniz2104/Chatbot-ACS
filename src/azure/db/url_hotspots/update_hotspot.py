import logging
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlparse

from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableServiceClient, UpdateMode

from src.azure.db.table_client import TABLE_URL_HOTSPOTS
from src.azure.error_handlers import resource_exists
from src.azure.kv.get_secrets_from_kv import get_storage_account_secret

logger = logging.getLogger(__name__)


def _partition_key(url: str) -> str:
    return urlparse(url).hostname or "unknown"


def _row_key(url: str) -> str:
    return sha256(url.encode()).hexdigest()[:32]


def _increment(client, partition_key: str, row_key: str, url: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    try:
        entity = client.get_entity(partition_key, row_key)
        entity["count"] = entity.get("count", 0) + 1
        entity["last_updated"] = now
        client.update_entity(entity, mode=UpdateMode.MERGE)
    except ResourceNotFoundError:
        client.create_entity({
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "url": url,
            "count": 1,
            "last_updated": now,
        })


def update_hotspot(urls: list[str]) -> None:
    if not urls:
        return
    try:
        conn = get_storage_account_secret()
        service = TableServiceClient.from_connection_string(conn)
        with resource_exists():
            service.create_table(TABLE_URL_HOTSPOTS)
        client = service.get_table_client(TABLE_URL_HOTSPOTS)
        for url in urls:
            try:
                _increment(client, _partition_key(url), _row_key(url), url)
            except Exception as e:
                logger.warning("[HOTSPOT] Failed to update %s: %s", url, e)
        logger.info("[HOTSPOT] Updated %d URL(s)", len(urls))
    except Exception as e:
        logger.error("[HOTSPOT] update_hotspot failed: %s", e)
