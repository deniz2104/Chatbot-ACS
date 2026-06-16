from datetime import datetime, timezone

import bcrypt
from azure.core.exceptions import ResourceExistsError

from src.azure.db.table_client import get_table_client

def register_user(
    connection_string: str,
    username: str,
    password: str,
    year: int,
    department: str,
    student_class: str,
) -> bool:
    client = get_table_client(connection_string)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    entity = {
        "PartitionKey": "user",
        "RowKey": username,
        "password_hash": hashed,
        "year": year,
        "department": department,
        "student_class": student_class,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": "",
    }
    try:
        client.create_entity(entity)
        return True
    except ResourceExistsError:
        return False
