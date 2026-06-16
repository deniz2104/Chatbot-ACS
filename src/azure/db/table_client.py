import streamlit as st
from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError

TABLE_USERS = "users"
TABLE_CONVERSATIONS = "conversations"

@st.cache_resource
def _get_service_client(connection_string: str) -> TableServiceClient:
    return TableServiceClient.from_connection_string(connection_string)

def get_table_client(connection_string: str) -> TableClient:
    return _get_service_client(connection_string).get_table_client(TABLE_USERS)

def get_conversations_table_client(connection_string: str) -> TableClient:
    return _get_service_client(connection_string).get_table_client(TABLE_CONVERSATIONS)

def init_tables(connection_string: str) -> None:
    service = _get_service_client(connection_string)
    for table in (TABLE_USERS, TABLE_CONVERSATIONS):
        try:
            service.create_table(table)
        except ResourceExistsError:
            pass
