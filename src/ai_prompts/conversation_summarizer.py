import logging

import anthropic

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL
from src.ai_prompts.utils import make_ai_template

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Ești un asistent care rezumă conversații în limba română. "
    "Folosește întotdeauna instrumentul pus la dispoziție."
)

_SUMMARIZE_TOOL = {
    "name": "summarize_conversation",
    "description": "Rezumează o conversație în titlu și sumar.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Titlu scurt, maxim 5 cuvinte, în română cu diacritice corecte.",
            },
            "summary": {
                "type": "string",
                "description": "Rezumat de 2-3 propoziții, în română cu diacritice corecte.",
            },
        },
        "required": ["title", "summary"],
    },
}


def summarize_conversation(messages: list[dict]) -> dict | None:
    if not messages:
        return None

    conversation_text = "\n".join(
        f"{'Utilizator' if m['role'] == 'user' else 'Asistent'}: {m['content']}"
        for m in messages
    )

    template = make_ai_template(
        system_prompt=_SYSTEM_PROMPT,
        tokens=256,
        tools=[_SUMMARIZE_TOOL],
        tool_choice={"type": "tool", "name": "summarize_conversation"},
        content=conversation_text[:4000],
        model=_SONNET_MODEL,
    )

    try:
        response = _CLIENT.messages.create(**template.to_dict())
        for block in response.content:
            if block.type == "tool_use" and block.name == "summarize_conversation":
                return block.input
        logger.warning("[SUMMARIZER] No tool_use block in response")
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
