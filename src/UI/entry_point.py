import streamlit as st

from src.azure.kv.get_secrets_from_kv import get_storage_account_secret
from src.UI.login_page import render_login
from src.UI.register_page import render_register
from src.UI.forgot_password_page import render_forgot_password
from src.UI.render_chat_page import render_chat_page
from src.UI.set_initial_session import set_initial_session
from src.UI.user_session import verify_session
from src.UI.prerequities import set_initial_prerequities

@st.cache_resource
def get_connection_string() -> str:
    return get_storage_account_secret()

def main() -> None:
    connection_string = get_connection_string()
    set_initial_prerequities()
    set_initial_session(connection_string)
    verify_session(connection_string)

    if st.session_state.user:
        render_chat_page(connection_string)
        return

    pages = {
        "login": render_login,
        "register": render_register,
        "forgot": render_forgot_password
    }
    pages.get(st.session_state.auth_page, render_login)(connection_string)


if __name__ == "__main__":
    main()
