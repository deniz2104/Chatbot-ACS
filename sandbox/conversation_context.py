import streamlit as st


def save_conversation_context() -> None:
    # Mock: no DB, just clear in-memory messages
    st.session_state.messages = []
