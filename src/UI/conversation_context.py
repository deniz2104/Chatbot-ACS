import logging

import streamlit as st

from src.azure.db.update_conversations import update_conversation_summary
from src.azure.db.load_user_conversations import load_user_conversations
from src.ai_prompts.conversation_summarizer import summarize_conversation

logger = logging.getLogger(__name__)

def save_conversation_context(connection_string: str) -> None:
    messages = st.session_state.get("messages", [])
    if not messages:
        return

    user = st.session_state.get("user")
    conversation_id = st.session_state.get("conversation_id")
    if not user or not conversation_id:
        return

    username = user["RowKey"]

    result = summarize_conversation(messages)
    if not result:
        logger.warning("[CTX] Could not summarize conversation %s — saving messages without title/summary", conversation_id)

    update_conversation_summary(
        connection_string,
        username,
        conversation_id,
        messages,
        result["title"] if result else "",
        result["summary"] if result else "",
    )

    st.session_state.messages = []
    st.session_state.conversations = load_user_conversations(connection_string, username)

    logger.info("[CTX] Saved conversation %s for user %s", conversation_id, username)
