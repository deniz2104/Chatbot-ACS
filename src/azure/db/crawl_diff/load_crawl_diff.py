import json

import streamlit as st

from src.azure.db.table_client import get_crawl_diffs_table_client
from src.azure.error_handlers import resource_not_found


@st.cache_data(ttl=300)
def load_latest_crawl_diff(connection_string: str) -> dict | None:
    client = get_crawl_diffs_table_client(connection_string)
    entities = []
    with resource_not_found():
        entities = list(client.query_entities("PartitionKey eq 'global'"))
    if not entities:
        return None
    latest = max(entities, key=lambda e: e["RowKey"])
    return {
        "crawled_at": latest.get("crawled_at", ""),
        "new_urls": json.loads(latest.get("new_urls", "[]")),
        "changed_urls": json.loads(latest.get("changed_urls", "[]")),
        "removed_urls": json.loads(latest.get("removed_urls", "[]")),
        "new_count": latest.get("new_count", 0),
        "changed_count": latest.get("changed_count", 0),
        "removed_count": latest.get("removed_count", 0),
        "unchanged_count": latest.get("unchanged_count", 0),
    }
