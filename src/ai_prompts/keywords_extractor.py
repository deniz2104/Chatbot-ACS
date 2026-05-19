import dataclasses
import logging
import json
from functools import lru_cache

import anthropic

from src.ai_prompts.constants import _CLIENT
from src.ai_prompts.utils import _extract_ai_text, make_ai_template

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a keyword extraction assistant.\n\n"
    "Given a piece of text (a webpage or a user query), extract the most relevant keywords and key phrases.\n\n"
    "Rules:\n"
    "- Output only a JSON array of strings, e.g. [\"keyword one\", \"keyword two\"]\n"
    "- Include specific terms, topics, and named entities\n"
    "- Normalize to lowercase\n"
    "- No duplicates\n"
    "- No explanation or extra output — only the JSON array\n"
    "- If no meaningful keywords can be extracted, output []"
    "- Output the keywords in Romanian, make sure to include diacritics where appropriate"
)

@lru_cache(maxsize=256)
def extract_keywords(content: str, tokens: int = 128) -> list[str]:
    if not content.strip():
        return []

    template = make_ai_template(_SYSTEM_PROMPT, tokens=tokens, content=content[:6000])

    try:
        response = _CLIENT.messages.create(**dataclasses.asdict(template))
        raw = _extract_ai_text(response)
    except anthropic.AuthenticationError:
        logger.error("[KEYWORDS] Invalid API key — check ANTHROPIC_API_KEY")
        raise
    except anthropic.RateLimitError:
        logger.warning("[KEYWORDS] Rate limit hit, returning empty keywords")
        return []
    except anthropic.APIConnectionError:
        logger.warning("[KEYWORDS] API connection failed, returning empty keywords")
        return []
    except anthropic.APIStatusError as e:
        logger.warning("[KEYWORDS] API error %s, returning empty keywords", e.status_code)
        return []

    try:
        keywords = json.loads(raw)
        if isinstance(keywords, list):
            return [k for k in keywords if isinstance(k, str)]
        logger.warning("[KEYWORDS] Unexpected JSON shape from LLM: %s", raw[:100])
    except json.JSONDecodeError:
        logger.warning("[KEYWORDS] LLM returned non-JSON: %s", raw[:100])

    return []
