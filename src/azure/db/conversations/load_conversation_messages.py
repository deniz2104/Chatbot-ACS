import json
import logging

from src.azure.db.table_client import get_conversations_table_client
from src.azure.error_handlers import resource_not_found

logger = logging.getLogger(__name__)

def load_conversation_messages(connection_string: str, username: str, conversation_id: str) -> list[dict]:
    client = get_conversations_table_client(connection_string)
    entity = None
    with resource_not_found():
        entity = dict(client.get_entity(partition_key=username, row_key=conversation_id))
    if entity is None:
        logger.warning("[CONV] Conversation %s not found for user %s", conversation_id, username)
        return []
    return json.loads(entity.get("messages", "[]"))
