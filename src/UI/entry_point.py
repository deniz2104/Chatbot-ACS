import streamlit as st

from src.azure.kv.get_secrets_from_kv import get_storage_account_secret
from src.UI.views.upb_login_page import render_upb_login
from src.UI.views.login_page import render_login
from src.UI.views.register_page import render_register
from src.UI.views.forgot_password_page import render_forgot_password
from src.UI.render.render_chat_page import render_chat_page
from src.UI.session.set_initial_session import set_initial_session
from src.UI.session.user_session import verify_session
from src.UI.prerequities import set_initial_prerequities
from src.UI.session.cookie_session import init_cookie_manager, restore_session_from_cookie
from src.UI.render.render_welcome import render_welcome
from src.vector_database.query import initialize_query

@st.cache_resource
def get_connection_string() -> str:
    return get_storage_account_secret()

@st.cache_resource
def _warm_up_reranker() -> None:
    initialize_query()

def main() -> None:
    connection_string = get_connection_string()
    _warm_up_reranker()
    set_initial_prerequities()
    init_cookie_manager()
    set_initial_session(connection_string)
    restore_session_from_cookie(connection_string)

    if not st.session_state.get("user") and not st.session_state.get("_cookie_restore_attempted"):
        st.session_state._cookie_restore_attempted = True
        st.rerun()

    verify_session(connection_string)

    if st.session_state.user:
        if st.session_state.get("show_welcome"):
            render_welcome()
            return
        render_chat_page(connection_string)
        return

    pages = {
        "upb_login": render_upb_login,
        "login": render_login,
        "register": render_register,
        "forgot": render_forgot_password,
    }
    pages.get(st.session_state.auth_page, render_upb_login)(connection_string)


if __name__ == "__main__":
    main()
