import streamlit as st
from src.UI.conversation_context import save_conversation_context
from src.chatbot.session import reset_session

def delete_session(connection_string: str) -> None:
    save_conversation_context(connection_string)
    st.session_state.clear()
    reset_session()
