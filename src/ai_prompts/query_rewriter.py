import dataclasses
import logging
import unicodedata
from functools import lru_cache

import anthropic

from src.ai_prompts.constants import _CLIENT
from src.ai_prompts.utils import _extract_ai_text, make_ai_template

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ești un asistent care normalizează interogări în limba română.\n\n"
    "Rescrie interogarea utilizatorului respectând aceste reguli:\n"
    "- Corectează diacriticele românești (ă, â, î, ș, ț) acolo unde lipsesc\n"
    "- Corectează greșelile de ortografie\n"
    "- Extinde abrevierile comune\n"
    "- Transformă limbajul informal sau prescurtat în formulări clare\n"
    "- Păstrează intenția și sensul original\n"
    "- Returnează DOAR interogarea rescrisă, fără explicații sau text suplimentar"
)

def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower().strip()

@lru_cache(maxsize=256)
def _rewrite_normalized(query: str) -> str:
    template = make_ai_template(_SYSTEM_PROMPT, tokens=256, content=query)
    try:
        response = _CLIENT.messages.create(**dataclasses.asdict(template))
        rewritten = _extract_ai_text(response)
        if rewritten:
            logger.debug("[QUERY REWRITE] '%s' -> '%s'", query, rewritten)
            return _normalize_unicode(rewritten)
    except anthropic.AuthenticationError:
        logger.error("[QUERY REWRITE] Invalid API key — check ANTHROPIC_API_KEY")
        raise
    except anthropic.RateLimitError:
        logger.warning("[QUERY REWRITE] Rate limit hit, using original query")
    except anthropic.APIConnectionError:
        logger.warning("[QUERY REWRITE] API connection failed, using original query")
    except anthropic.APIStatusError as e:
        logger.warning("[QUERY REWRITE] API error %s, using original query", e.status_code)
    return query


def rewrite_query(query: str) -> str:
    query = _normalize_unicode(query)
    if not query:
        return query
    return _rewrite_normalized(query)
