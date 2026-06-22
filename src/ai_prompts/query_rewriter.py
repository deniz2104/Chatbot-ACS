import dataclasses
import json
import logging
import unicodedata
from functools import lru_cache

import anthropic

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL
from src.ai_prompts.utils import _extract_ai_text, make_ai_template

logger = logging.getLogger(__name__)

_REWRITE_PROMPT = (
    "Ești un asistent care normalizează interogări în limba română.\n\n"
    "Rescrie interogarea utilizatorului respectând aceste reguli:\n"
    "- Corectează diacriticele românești (ă, â, î, ș, ț) acolo unde lipsesc\n"
    "- Corectează greșelile de ortografie\n"
    "- Extinde abrevierile comune\n"
    "- Transformă limbajul informal sau prescurtat în formulări clare\n"
    "- Păstrează intenția și sensul original\n"
    "- Returnează DOAR interogarea rescrisă, fără explicații sau text suplimentar"
)

_DECOMPOSE_PROMPT = (
    "Ești un asistent care desparte întrebările compuse din limba română în sub-întrebări independente.\n\n"
    "COMPORTAMENT IMPLICIT: Dacă întrebarea conține conjuncția 'și', 'dar', 'dar și', 'de asemenea' "
    "sau 'totodată' care unește două cereri de informații distincte, DESPARTE-LE obligatoriu.\n\n"
    "Desparte întrebarea dacă:\n"
    "- Cele două părți vizează aspecte diferite (ex. persoană vs. dată, materie vs. credite, "
    "procedură vs. documente necesare, sală vs. profesor)\n"
    "- Prima parte rămâne o întrebare validă și completă fără a doua parte\n"
    "- Cele două părți ar fi găsite în surse de informații diferite\n\n"
    "Nu despărți dacă 'și' face parte dintr-o enumerare în cadrul aceleiași cereri de informație "
    "(ex. 'care sunt avantajele și dezavantajele X?' este o singură întrebare).\n\n"
    "Fiecare sub-întrebare trebuie să fie completă și de sine stătătoare, "
    "repetând contextul necesar (subiectul, materia, specializarea) dacă este nevoie.\n\n"
    "Returnează DOAR o listă JSON de string-uri, fără explicații sau text suplimentar. "
    "Dacă întrebarea este atomică, lista conține un singur element."
)


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower().strip()


@lru_cache(maxsize=256)
def _rewrite_normalized(query: str) -> str:
    template = make_ai_template(_REWRITE_PROMPT, tokens=256, content=query)
    try:
        response = _CLIENT.messages.create(**template.to_dict())
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


@lru_cache(maxsize=256)
def _decompose_normalized(query: str) -> tuple[str, ...]:
    template = make_ai_template(_DECOMPOSE_PROMPT, tokens=512, content=query, model=_SONNET_MODEL)
    try:
        response = _CLIENT.messages.create(**template.to_dict())
        raw = _extract_ai_text(response)
        parts = json.loads(raw)
        if isinstance(parts, list) and parts and all(isinstance(p, str) for p in parts):
            logger.debug("[QUERY DECOMPOSE] '%s' -> %s", query, parts)
            return tuple(parts)
    except json.JSONDecodeError:
        logger.warning("[QUERY DECOMPOSE] Invalid JSON for '%s', using original", query)
    except anthropic.AuthenticationError:
        logger.error("[QUERY DECOMPOSE] Invalid API key")
        raise
    except anthropic.RateLimitError:
        logger.warning("[QUERY DECOMPOSE] Rate limit hit, using original query")
    except anthropic.APIConnectionError:
        logger.warning("[QUERY DECOMPOSE] API connection failed, using original query")
    except anthropic.APIStatusError as e:
        logger.warning("[QUERY DECOMPOSE] API error %s, using original query", e.status_code)
    return (query,)


def rewrite_query(query: str) -> str:
    query = _normalize_unicode(query)
    if not query:
        return query
    return _rewrite_normalized(query)


def decompose_query(query: str) -> list[str]:
    query = _normalize_unicode(query)
    if not query:
        return [query]
    return list(_decompose_normalized(query))
