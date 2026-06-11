import dataclasses
import json
import logging

import anthropic

from src.ai_prompts.constants import _CLIENT
from src.ai_prompts.utils import _extract_ai_text, make_ai_template

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ești un asistent care rezumă conversații.\n\n"
    "Analizează conversația furnizată și returnează DOAR un JSON valid cu structura:\n"
    '{"title": "titlu scurt maxim 5 cuvinte", "summary": "rezumat 2-3 propoziții"}\n\n'
    "Titlul și rezumatul trebuie să fie în română cu diacritice corecte.\n"
    "Nu adăuga text suplimentar în afara JSON-ului."
)

def summarize_conversation(messages: list[dict]) -> dict | None:
    if not messages:
        return None

    conversation_text = "\n".join(
        f"{'Utilizator' if m['role'] == 'user' else 'Asistent'}: {m['content']}"
        for m in messages
    )

    template = make_ai_template(
        _SYSTEM_PROMPT,
        tokens=256,
        content=conversation_text[:4000],
    )

    try:
        response = _CLIENT.messages.create(**dataclasses.asdict(template))
        raw = _extract_ai_text(response)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(cleaned)
        if isinstance(result, dict) and "title" in result and "summary" in result:
            return result
        logger.warning("[SUMMARIZER] Unexpected JSON shape: %s", raw[:100])
    except json.JSONDecodeError:
        logger.warning("[SUMMARIZER] Non-JSON response: %s", raw[:100])
    except anthropic.AuthenticationError:
        logger.error("[SUMMARIZER] Invalid API key")
        raise
    except anthropic.RateLimitError:
        logger.warning("[SUMMARIZER] Rate limit hit")
    except anthropic.APIConnectionError:
        logger.warning("[SUMMARIZER] API connection failed")
    except anthropic.APIStatusError as e:
        logger.warning("[SUMMARIZER] API error %s", e.status_code)

    return None
