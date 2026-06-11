from src.secrets.kv_instance import get_kv_client
from src.utils.singleton import make_singleton


def _fetch(name: str) -> str:
    return get_kv_client().get_secret(name).value

get_llm_api_key = make_singleton(lambda: _fetch("llm-api-key"))
get_redis_url = make_singleton(lambda: _fetch("redis-url"))
general_file_store = make_singleton(lambda: _fetch("files-store"))
chatbot_file_store = make_singleton(lambda: _fetch("scrapy-files-store"))
get_hugging_face_token = make_singleton(lambda: _fetch("hugging-face-token"))
get_storage_account_secret = make_singleton(lambda: _fetch("storage-account-secret"))
