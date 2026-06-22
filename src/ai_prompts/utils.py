import dataclasses
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
    tools: list[dict] | None = None
    tool_choice: dict | None = None

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        return {k: v for k, v in d.items() if v is not None}


def _extract_ai_text(response) -> str:
    return next((b.text for b in response.content if b.type == "text"), "").strip()


def make_ai_template(
    system_prompt: str,
    tokens: int,
    tools: list[dict] | None = None,
    tool_choice: dict | None = None,
    temperature: float = 0.0,
    content: str = "",
    messages: list[dict] | None = None,
    model=_HAIKU_MODEL,
) -> AIResponseTemplate:
    return AIResponseTemplate(
        model=model,
        max_tokens=tokens,
        tools=tools,
        tool_choice=tool_choice,
        temperature=temperature,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=messages if messages is not None else [{"role": "user", "content": content}],
    )
