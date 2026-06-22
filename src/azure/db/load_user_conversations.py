from src.azure.db.table_client import get_conversations_table_client

def load_user_conversations(connection_string: str, username: str) -> list[dict]:
    client = get_conversations_table_client(connection_string)
    entities = client.query_entities(f"PartitionKey eq '{username}'")
    conversations = [dict(e) for e in entities]
    conversations = [
        c for c in conversations
        if c.get("title") or c.get("messages", "[]") != "[]"
    ]
    conversations.sort(key=lambda c: c.get("last_active", ""), reverse=True)
    return conversations
