from azure.storage.blob import BlobServiceClient

from src.azure.error_handlers import resource_exists
from src.azure.storage_account.set_blob_service import blob_service_client

def create_blob_container(client: BlobServiceClient = blob_service_client(), container_name: str = "chatbot"):
    with resource_exists():
        client.create_container(name=container_name)