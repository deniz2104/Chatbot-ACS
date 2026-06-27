import json
import logging
from datetime import datetime, timezone

from azure.data.tables import TableServiceClient

from src.azure.db.table_client import TABLE_CRAWL_DIFFS
from src.azure.error_handlers import resource_exists
from src.azure.kv.get_secrets_from_kv import get_storage_account_secret

logger = logging.getLogger(__name__)

_MAX_URLS_STORED = 300


def _truncate(urls: set[str]) -> list[str]:
    return sorted(urls)[:_MAX_URLS_STORED]


def save_crawl_diff(
    new_urls: set[str],
    changed_urls: set[str],
    removed_urls: set[str],
    unchanged_count: int,
) -> None:
    try:
        connection_string = get_storage_account_secret()
        service = TableServiceClient.from_connection_string(connection_string)
        with resource_exists():
            service.create_table(TABLE_CRAWL_DIFFS)

        n_new, n_changed, n_removed = len(new_urls), len(changed_urls), len(removed_urls)
        now = datetime.now(timezone.utc)
        entity = {
            "PartitionKey": "global",
            "RowKey": now.strftime("%Y%m%dT%H%M%SZ"),
            "crawled_at": now.isoformat(),
            "new_urls": json.dumps(_truncate(new_urls)),
            "changed_urls": json.dumps(_truncate(changed_urls)),
            "removed_urls": json.dumps(_truncate(removed_urls)),
            "new_count": n_new,
            "changed_count": n_changed,
            "removed_count": n_removed,
            "unchanged_count": unchanged_count,
        }
        service.get_table_client(TABLE_CRAWL_DIFFS).create_entity(entity)
        logger.info(
            "[CRAWL DIFF] Saved — new: %d | changed: %d | removed: %d",
            n_new, n_changed, n_removed,
        )
    except Exception as e:
        logger.error("[CRAWL DIFF] Failed to save crawl diff: %s", e)
