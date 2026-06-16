from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from src.azure.storage_account.constants import STORAGE_ACCOUNT_NAME
from src.utils.singleton import make_singleton

def set_blob_service() -> BlobServiceClient:
    return BlobServiceClient(account_url=STORAGE_ACCOUNT_NAME, credential=DefaultAzureCredential())

blob_service_client = make_singleton(set_blob_service)