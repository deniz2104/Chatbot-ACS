import streamlit as st
from datetime import datetime, timezone

from src.azure.db.auth.login_user import login_user
from src.UI.conversation.conversation import create_user_conversation, conversation_history
from src.UI.session.cookie_session import set_session_cookie
from src.UI.utils import navigate_to


def render_login(connection_string: str) -> None:
    st.title("Login")

    upb = st.session_state.get("upb_verified", {})

    if upb:
        st.success(f"Identitate UPB confirmată pentru **{upb.get('email', '')}**.")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not username or not password:
            st.error("Completează toate câmpurile.")
            return

        user = login_user(connection_string, username, password)
        if user is None:
            st.error("Username sau parolă incorecte.")
            return

        st.session_state.pop("upb_verified", None)
        st.session_state.user = user
        st.session_state.login_time = datetime.now(timezone.utc)
        st.session_state.show_welcome = True
        set_session_cookie(connection_string)
        create_user_conversation(connection_string)
        conversation_history(connection_string)
        st.stop()

    st.divider()

    if st.button("Parolă uitată", use_container_width=True):
        navigate_to("forgot")
