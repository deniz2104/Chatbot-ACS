import logging
from functools import lru_cache

from src.ai_prompts.constants import _CLIENT
from src.ai_prompts.error_handlers import anthropic_call
from src.ai_prompts.utils import _extract_ai_text, make_ai_template

logger = logging.getLogger(__name__)

_HYDE_PROMPT = (
    "Ești un document oficial al Facultății de Automatică și Calculatoare (ACS) "
    "din cadrul Universității Politehnica București.\n\n"
    "Generează un scurt paragraf în română (3-5 propoziții) care ar putea apărea "
    "pe site-ul oficial al facultății și care conține răspunsul la întrebarea primită.\n"
    "Respectă aceste reguli:\n"
    "- Scrie în stilul unui document academic oficial, nu conversațional\n"
    "- Folosește terminologia specifică facultății: serie, grupă, titular de curs, "
    "plan de învățământ, credite ECTS, sesiune, restanță, colocviu, catedră, "
    "decan, secretariat, fișa disciplinei, prelegere, seminar, laborator\n"
    "- Dacă nu cunoști detaliile exacte, generează informații plauzibile și coerente\n"
    "- Folosește diacritice românești corecte\n"
    "- Returnează DOAR paragraful, fără titlu, introducere sau explicații"
)


@lru_cache(maxsize=256)
def generate_hypothetical_doc(query: str) -> str:
    template = make_ai_template(_HYDE_PROMPT, tokens=300, content=query)
    with anthropic_call("HYDE"):
        response = _CLIENT.messages.create(**template.to_dict())
        doc = _extract_ai_text(response)
        if doc:
            logger.debug("[HYDE] Generated %d chars for: '%s'", len(doc), query[:60])
            return doc
    return query
