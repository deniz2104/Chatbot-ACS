from azure.core.exceptions import ResourceNotFoundError

from src.DB.table_client import get_table_client

def username_exists(connection_string: str, username: str) -> bool:
    client = get_table_client(connection_string)
    try:
        client.get_entity(partition_key="user", row_key=username)
        return True
    except ResourceNotFoundError:
        return False
