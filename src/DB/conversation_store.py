import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from src.DB.table_client import get_conversations_table_client

logger = logging.getLogger(__name__)

def create_conversation(connection_string: str, username: str) -> str:
    conversation_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    entity = {
        "PartitionKey": username,
        "RowKey": conversation_id,
        "messages": json.dumps([]),
        "title": "",
        "summary": "",
        "created_at": now,
        "last_active": now,
    }
    client = get_conversations_table_client(connection_string)
    client.create_entity(entity)
    logger.debug("[CONV] Created conversation %s for user %s", conversation_id, username)
    return conversation_id
