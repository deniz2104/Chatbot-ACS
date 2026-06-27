from datetime import datetime, timezone

import bcrypt

from src.azure.db.table_client import get_table_client
from src.azure.error_handlers import resource_exists

def register_user(
    connection_string: str,
    username: str,
    first_name: str,
    last_name: str,
    password: str,
    year: int,
    department: str,
    student_class: str,
    email: str,
) -> bool:
    client = get_table_client(connection_string)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    entity = {
        "PartitionKey": "user",
        "RowKey": username,
        "first_name": first_name,
        "last_name": last_name,
        "password_hash": hashed,
        "year": year,
        "department": department,
        "student_class": student_class,
        "email": email.lower(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": "",
    }
    with resource_exists():
        client.create_entity(entity)
        return True
    return False
