from dataclasses import dataclass
from anthropic.types import MessageParam, TextBlockParam
from src.ai_prompts.constants import _HAIKU_MODEL


@dataclass
class AIResponseTemplate:
    model: str
    max_tokens: int
    temperature: float
    system: list[TextBlockParam]
    messages: list[MessageParam]


def _extract_ai_text(response) -> str:
    return next((b.text for b in response.content if b.type == "text"), "").strip()


def make_ai_template(
    system_prompt: str,
    tokens: int,
    temperature: float = 0.0,
    content: str = "",
    model=_HAIKU_MODEL,
) -> AIResponseTemplate:
    return AIResponseTemplate(
        model=model,
        max_tokens=tokens,
        temperature=temperature,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": content}],
    )
