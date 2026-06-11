from datetime import datetime, timezone

import bcrypt
from azure.core.exceptions import ResourceNotFoundError

from src.DB.table_client import get_table_client

def login_user(
    connection_string: str,
    username: str,
    password: str,
) -> dict | None:
    client = get_table_client(connection_string)
    try:
        entity = dict(client.get_entity(partition_key="user", row_key=username))
    except ResourceNotFoundError:
        return None

    stored_hash: str = entity.get("password_hash", "")
    if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return None

    entity["last_login"] = datetime.now(timezone.utc).isoformat()
    client.upsert_entity(entity)

    entity.pop("password_hash", None)
    return entity
