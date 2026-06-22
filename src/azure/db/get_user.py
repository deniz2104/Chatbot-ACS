from azure.core.exceptions import ResourceNotFoundError

from src.azure.db.table_client import get_table_client

def get_user(connection_string: str, username: str) -> dict | None:
    client = get_table_client(connection_string)
    try:
        entity = dict(client.get_entity(partition_key="user", row_key=username))
    except ResourceNotFoundError:
        return None
    entity.pop("password_hash", None)
    return entity
