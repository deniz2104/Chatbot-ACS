import bcrypt

from src.azure.db.table_client import get_table_client
from src.azure.error_handlers import resource_not_found

def update_password(
    connection_string: str,
    username: str,
    new_password: str,
) -> bool:
    client = get_table_client(connection_string)
    with resource_not_found():
        entity = dict(client.get_entity(partition_key="user", row_key=username))
        entity["password_hash"] = bcrypt.hashpw(
            new_password.encode(), bcrypt.gensalt()
        ).decode()
        client.upsert_entity(entity)
        return True
    return False
