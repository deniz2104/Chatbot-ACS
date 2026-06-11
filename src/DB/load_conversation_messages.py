import json
import logging

from azure.core.exceptions import ResourceNotFoundError

from src.DB.table_client import get_conversations_table_client

logger = logging.getLogger(__name__)

def load_conversation_messages(connection_string: str, username: str, conversation_id: str) -> list[dict]:
    client = get_conversations_table_client(connection_string)
    try:
        entity = dict(client.get_entity(partition_key=username, row_key=conversation_id))
    except ResourceNotFoundError:
        logger.warning("[CONV] Conversation %s not found for user %s", conversation_id, username)
        return []

    return json.loads(entity.get("messages", "[]"))
