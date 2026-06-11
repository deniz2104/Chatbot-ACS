import streamlit as st
from src.DB.conversation_store import create_conversation
from src.DB.load_user_conversations import load_user_conversations

def create_user_conversation(connection_string: str) -> None:
    username = st.session_state.user["RowKey"]
    conversation_id = create_conversation(connection_string, username)
    st.session_state.conversation_id = conversation_id
    st.session_state.loaded_conversation_id = conversation_id
    st.session_state.messages = []

def conversation_history(connection_string: str) -> None:
    username = st.session_state.user["RowKey"]
    st.session_state.conversations = load_user_conversations(connection_string, username)
