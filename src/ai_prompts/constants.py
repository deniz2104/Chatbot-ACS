import anthropic

from src.secrets.get_secrets_from_kv import get_llm_api_key

_CLIENT = anthropic.Anthropic(api_key=get_llm_api_key())
_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_SONNET_MODEL = "claude-sonnet-4-6"
_NUMBER_OF_CONVERSATIONS = 20
