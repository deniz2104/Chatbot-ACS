import json
import logging
import unicodedata
from functools import lru_cache

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL
from src.ai_prompts.error_handlers import anthropic_call
from src.ai_prompts.utils import _extract_ai_text, make_ai_template

logger = logging.getLogger(__name__)

_REWRITE_PROMPT = (
    "Ești un asistent care normalizează interogări în limba română.\n\n"
    "Rescrie interogarea utilizatorului respectând aceste reguli:\n"
    "- Corectează diacriticele românești (ă, â, î, ș, ț) acolo unde lipsesc în cuvintele comune\n"
    "- Corectează greșelile de ortografie\n"
    "- Extinde abrevierile comune\n"
    "- Transformă limbajul informal sau prescurtat în formulări clare\n"
    "- Păstrează intenția și sensul original\n"
    "- IMPORTANT: Nu modifica și nu adăuga diacritice la cuvintele care încep cu literă mare "
    "sau sunt scrise complet cu majuscule — acestea sunt nume proprii (prenume, nume de familie, "
    "denumiri) și trebuie păstrate exact cum apar în interogare\n"
    "- Returnează DOAR interogarea rescrisă, fără explicații sau text suplimentar"
)

_RESOLVE_PROMPT = (
    "Ești un asistent care rezolvă referințele din întrebări de urmărire în limba română.\n\n"
    "Primești istoricul conversației și o întrebare nouă. Dacă întrebarea conține pronume "
    "sau referințe vagi (el, ea, acesta, aceasta, același, cursurile lui, programul ei, etc.) "
    "care trimit la ceva din istoricul conversației, rescrie întrebarea astfel încât să fie "
    "completă și de sine stătătoare — înlocuiește pronumele cu termenii expliciți din istoric.\n\n"
    "Dacă întrebarea este deja de sine stătătoare sau istoricul nu conține context relevant, "
    "returnează întrebarea neschimbată.\n\n"
    "Returnează DOAR întrebarea rezolvată, fără explicații sau text suplimentar."
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

def _resolve_followup(query: str, history: list[dict]) -> str:
    if not history:
        return query

    history_text = "\n".join(
        f"{'Utilizator' if m['role'] == 'user' else 'Asistent'}: {m['content']}"
        for m in history
    )
    content = f"Istoricul conversației:\n{history_text}\n\nÎntrebarea curentă: {query}"
    template = make_ai_template(_RESOLVE_PROMPT, tokens=256, content=content)
    with anthropic_call("QUERY RESOLVE"):
        response = _CLIENT.messages.create(**template.to_dict())
        resolved = _extract_ai_text(response)
        if resolved:
            logger.debug("[QUERY RESOLVE] '%s' -> '%s'", query, resolved)
            return resolved
    return _normalize_unicode(query)


@lru_cache(maxsize=256)
def _rewrite_normalized(query: str) -> str:
    template = make_ai_template(_REWRITE_PROMPT, tokens=256, content=query)
    with anthropic_call("QUERY REWRITE"):
        response = _CLIENT.messages.create(**template.to_dict())
        rewritten = _extract_ai_text(response)
        if rewritten:
            logger.debug("[QUERY REWRITE] '%s' -> '%s'", query, rewritten)
            return _normalize_unicode(rewritten)
    return _normalize_unicode(query)


@lru_cache(maxsize=256)
def _decompose_normalized(query: str) -> tuple[str, ...]:
    template = make_ai_template(_DECOMPOSE_PROMPT, tokens=512, content=query, model=_SONNET_MODEL)
    with anthropic_call("QUERY DECOMPOSE"):
        response = _CLIENT.messages.create(**template.to_dict())
        raw = _extract_ai_text(response)
        try:
            parts = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("[QUERY DECOMPOSE] Invalid JSON for '%s', using original", query)
        else:
            if isinstance(parts, list) and parts and all(isinstance(p, str) for p in parts):
                logger.debug("[QUERY DECOMPOSE] '%s' -> %s", query, parts)
                return tuple(parts)
    return (query,)


def rewrite_query(query: str, history: list[dict] | None = None) -> str:
    query = _normalize_unicode(query)
    if history:
        query = _resolve_followup(query, history)
    
    return _rewrite_normalized(query)


def decompose_query(query: str) -> list[str]:
    query = _normalize_unicode(query)
    return list(_decompose_normalized(query))
