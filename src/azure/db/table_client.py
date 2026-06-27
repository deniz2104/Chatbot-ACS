import streamlit as st
from azure.data.tables import TableServiceClient, TableClient

from src.azure.error_handlers import resource_exists

TABLE_USERS = "users"
TABLE_CONVERSATIONS = "conversations"
TABLE_CRAWL_DIFFS = "crawldiffs"
TABLE_URL_HOTSPOTS = "urlhotspots"

@st.cache_resource
def _get_service_client(connection_string: str) -> TableServiceClient:
    return TableServiceClient.from_connection_string(connection_string)

def get_table_client(connection_string: str) -> TableClient:
    return _get_service_client(connection_string).get_table_client(TABLE_USERS)

def get_conversations_table_client(connection_string: str) -> TableClient:
    return _get_service_client(connection_string).get_table_client(TABLE_CONVERSATIONS)

def get_crawl_diffs_table_client(connection_string: str) -> TableClient:
    return _get_service_client(connection_string).get_table_client(TABLE_CRAWL_DIFFS)

def get_url_hotspots_table_client(connection_string: str) -> TableClient:
    return _get_service_client(connection_string).get_table_client(TABLE_URL_HOTSPOTS)

def init_tables(connection_string: str) -> None:
    service = _get_service_client(connection_string)
    for table in (TABLE_USERS, TABLE_CONVERSATIONS, TABLE_CRAWL_DIFFS, TABLE_URL_HOTSPOTS):
        with resource_exists():
            service.create_table(table)
