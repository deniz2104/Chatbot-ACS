import streamlit as st

from sandbox.login_page import render_login
from sandbox.register_page import render_register
from sandbox.forgot_password_page import render_forgot_password
from sandbox.render_chat_page import render_chat_page
from sandbox.set_initial_session import set_initial_session
from sandbox.user_session import verify_session
from sandbox.prerequities import set_initial_prerequities
from sandbox.conversation import conversation_history

set_initial_prerequities()


def main() -> None:
    set_initial_session()
    verify_session()

    if st.session_state.user:
        conversation_history()
        render_chat_page()
        return

    pages = {
        "login": render_login,
        "register": render_register,
        "forgot": render_forgot_password,
    }
    pages.get(st.session_state.auth_page, render_login)()


if __name__ == "__main__":
    main()
