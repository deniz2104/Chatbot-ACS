from datetime import datetime, timezone
import streamlit as st
from src.UI.constants import SESSION_LIFETIME
from src.UI.conversation.conversation_context import save_conversation_context
from src.UI.session.cookie_session import clear_session_cookie

def delete_session(connection_string: str) -> None:
    save_conversation_context(connection_string)
    clear_session_cookie()
    st.session_state.clear()

def _is_session_expired() -> bool:
    login_time: datetime | None = st.session_state.get("login_time")
    if login_time is None:
        return True
    return datetime.now(timezone.utc) - login_time > SESSION_LIFETIME

def verify_session(connection_string: str) -> None:
    if st.session_state.user and _is_session_expired():
        delete_session(connection_string)
        st.rerun()
