from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from src.azure.storage_account.set_blob_service import blob_service_client

def create_blob_container(blob_service_client: BlobServiceClient = blob_service_client(), container_name: str = "chatbot"):
    try:
        blob_service_client.create_container(name=container_name)
    except ResourceExistsError:
        print('A container with this name already exists')