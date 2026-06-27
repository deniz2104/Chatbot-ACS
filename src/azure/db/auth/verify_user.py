from src.azure.db.table_client import get_table_client
from src.azure.error_handlers import resource_not_found

def username_exists(connection_string: str, username: str) -> bool:
    client = get_table_client(connection_string)
    with resource_not_found():
        client.get_entity(partition_key="user", row_key=username)
        return True
    return False

def email_exists(connection_string: str, email: str) -> bool:
    client = get_table_client(connection_string)
    normalized = email.strip().lower()
    entities = client.query_entities(f"PartitionKey eq 'user' and email eq '{normalized}'")
    return any(True for _ in entities)

def email_matches(connection_string: str, username: str, email: str) -> bool:
    client = get_table_client(connection_string)
    with resource_not_found():
        entity = client.get_entity(partition_key="user", row_key=username)
        return entity.get("email", "").lower() == email.strip().lower()
    return False
