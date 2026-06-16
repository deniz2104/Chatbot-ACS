import bcrypt
from azure.core.exceptions import ResourceNotFoundError

from src.azure.db.table_client import get_table_client

def update_password(
    connection_string: str,
    username: str,
    new_password: str,
) -> bool:
    client = get_table_client(connection_string)
    try:
        entity = dict(client.get_entity(partition_key="user", row_key=username))
    except ResourceNotFoundError:
        return False

    entity["password_hash"] = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt()
    ).decode()
    client.upsert_entity(entity)
    return True
