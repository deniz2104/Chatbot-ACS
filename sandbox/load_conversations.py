import uuid
import streamlit as st


def setup_conversation_state() -> None:
    st.session_state.messages = []
    st.session_state.last_sources = []
    st.session_state.loaded_summary = ""


def load_conversation_history() -> None:
    st.session_state.past_conversations = st.session_state.get("past_conversations", [])
    st.session_state.conversation_id = str(uuid.uuid4())
    setup_conversation_state()


def switch_conversation(conversation_id: str) -> None:
    st.session_state.conversation_id = conversation_id
    setup_conversation_state()


def load_summary(conversation: dict) -> None:
    st.session_state.loaded_summary = conversation.get("summary", "")
