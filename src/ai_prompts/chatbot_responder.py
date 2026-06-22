import logging
from collections.abc import Generator

import anthropic
from langchain_core.documents import Document

from src.ai_prompts.constants import _CLIENT, _SONNET_MODEL, _NUMBER_OF_CONVERSATIONS
from src.ai_prompts.utils import make_ai_template

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a virtual assistant for the Faculty of Automation and Computer Science (ACS) "
    "at Politehnica University of Bucharest.\n\n"
    "You answer student questions about the faculty, study programs, exams, "
    "regulations, timetables, and other academic information.\n\n"
    "Use exclusively the information from the provided context. "
    "If you do not have relevant information, "
    "state that you cannot answer based on the available sources.\n\n"
    "Always respond in Romanian with correct diacritics."
)


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(
        f"[Sursă {i + 1}]: {doc.page_content}"
        for i, doc in enumerate(docs)
    )

def get_chatbot_response(
    user_query: str,
    docs: list[Document],
    history: list[dict],
    user_context: str = "",
    conversation_summary: str = "",
) -> Generator[str, None, None]:
    context = _format_docs(docs)
    user_content = (
        f"{user_query}\n\nInformații relevante din surse:\n{context}"
        if context else user_query
    )

    past_turns = history[-_NUMBER_OF_CONVERSATIONS:-1]
    llm_messages = past_turns + [{"role": "user", "content": user_content}]

    system_prompt = _SYSTEM_PROMPT
    if user_context:
        system_prompt += f"\n\nProfilul studentului: {user_context}."
    if conversation_summary:
        system_prompt += f"\n\nRezumatul conversației curente: {conversation_summary}"

    template = make_ai_template(
        system_prompt=system_prompt,
        tokens=1024,
        messages=llm_messages,
        model=_SONNET_MODEL,
    )

    try:
        with _CLIENT.messages.stream(**template.to_dict()) as stream:
            yield from stream.text_stream
    except anthropic.AuthenticationError:
        logger.error("[CHATBOT] Invalid API key")
        raise
    except anthropic.RateLimitError:
        logger.warning("[CHATBOT] Rate limit hit")
        yield "Sorry, the server is temporarily overloaded. Please try again."
    except anthropic.APIConnectionError:
        logger.warning("[CHATBOT] API connection failed")
        yield "Sorry, I cannot connect to the server. Please check your internet connection."
    except anthropic.APIStatusError as e:
        logger.warning("[CHATBOT] API error %s", e.status_code)
        yield "Sorry, an error occurred. Please try again."
