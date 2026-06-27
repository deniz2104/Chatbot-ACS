import streamlit as st
from datetime import datetime, timezone

from src.azure.db.auth.login_user import login_user
from src.UI.conversation.conversation import create_user_conversation, conversation_history
from src.UI.session.cookie_session import set_session_cookie
from src.UI.utils import navigate_to


def render_login(connection_string: str) -> None:
    st.title("Login")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not username or not password:
            st.error("Fill in all fields.")
            return

        user = login_user(connection_string, username, password)
        if user is None:
            st.error("Invalid username or password.")
            return

        st.session_state.user = user
        st.session_state.login_time = datetime.now(timezone.utc)
        st.session_state.show_welcome = True
        set_session_cookie(connection_string)
        create_user_conversation(connection_string)
        conversation_history(connection_string)
        st.stop()

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register", use_container_width=True):
            navigate_to("register")
    with col2:
        if st.button("Forgot Password", use_container_width=True):
            navigate_to("forgot")
