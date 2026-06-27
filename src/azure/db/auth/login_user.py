from datetime import datetime, timezone

import bcrypt

from src.azure.db.table_client import get_table_client
from src.azure.error_handlers import resource_not_found

def login_user(
    connection_string: str,
    username: str,
    password: str,
) -> dict | None:
    client = get_table_client(connection_string)
    with resource_not_found():
        entity = dict(client.get_entity(partition_key="user", row_key=username))
        stored_hash: str = entity.get("password_hash", "")
        if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return None
        entity["last_login"] = datetime.now(timezone.utc).isoformat()
        client.upsert_entity(entity)
        entity.pop("password_hash", None)
        return entity
    return None
