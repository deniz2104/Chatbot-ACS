from src.azure.db.table_client import get_table_client
from src.azure.error_handlers import resource_not_found

def get_user(connection_string: str, username: str) -> dict | None:
    client = get_table_client(connection_string)
    with resource_not_found():
        entity = dict(client.get_entity(partition_key="user", row_key=username))
        entity.pop("password_hash", None)
        return entity
    return None
