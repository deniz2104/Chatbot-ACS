from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from src.utils.singleton import make_singleton

def _build_kv_client() -> SecretClient:
    return SecretClient(vault_url="https://kv-chatbot-acs.vault.azure.net/", credential=DefaultAzureCredential())

get_kv_client = make_singleton(_build_kv_client)
