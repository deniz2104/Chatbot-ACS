import json
import logging
from datetime import datetime, timezone

from src.azure.db.table_client import get_conversations_table_client
from src.azure.error_handlers import resource_not_found

logger = logging.getLogger(__name__)

def update_conversation_summary(
    connection_string: str,
    username: str,
    conversation_id: str,
    messages: list[dict],
    title: str,
    summary: str,
) -> None:
    client = get_conversations_table_client(connection_string)
    entity = None
    with resource_not_found():
        entity = dict(client.get_entity(partition_key=username, row_key=conversation_id))
    if entity is None:
        logger.warning("[CONV] Conversation %s not found for user %s", conversation_id, username)
        return
    old_summary = entity.get("summary", "")
    old_title = entity.get("title", "")
    entity["messages"] = json.dumps(messages)
    entity["title"] = title or old_title
    entity["summary"] = summary or old_summary
    entity["last_active"] = datetime.now(timezone.utc).isoformat()
    client.upsert_entity(entity)
