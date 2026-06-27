from src.azure.kv.kv_instance import get_kv_client
from src.utils.singleton import make_singleton


def _fetch(name: str) -> str:
    return get_kv_client().get_secret(name).value

get_llm_api_key = make_singleton(lambda: _fetch("llm-api-key"))
get_file_store = make_singleton(lambda: _fetch("scrapy-files-store"))
get_redis_url = make_singleton(lambda: _fetch("redis-url"))
get_storage_account_secret = make_singleton(lambda: _fetch("storage-account-secret"))
get_acs_connection_string = make_singleton(lambda: _fetch("communication-connection-string"))
get_acs_sender_address = make_singleton(lambda: _fetch("email-sender-address"))
get_chroma_host = make_singleton(lambda: _fetch("chroma-host"))
