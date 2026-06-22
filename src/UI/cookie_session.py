import hashlib
from datetime import datetime, timezone

import jwt
import streamlit as st
import extra_streamlit_components as stx

from src.UI.constants import SESSION_LIFETIME, _COOKIE_NAME, _MANAGER_KEY
from src.azure.db.get_user import get_user
from src.UI.conversation import conversation_history


def init_cookie_manager() -> stx.CookieManager:
    manager = stx.CookieManager(key="cookie_manager")
    st.session_state[_MANAGER_KEY] = manager
    return manager

def _get_cookie_manager() -> stx.CookieManager:
    return st.session_state[_MANAGER_KEY]

def _jwt_secret(connection_string: str) -> str:
    return hashlib.sha256(connection_string.encode()).hexdigest()

def set_session_cookie(connection_string: str) -> None:
    username: str = st.session_state.user["RowKey"]
    login_time: datetime = st.session_state.login_time
    payload = {
        "sub": username,
        "iat": int(login_time.timestamp()),
        "exp": int((login_time + SESSION_LIFETIME).timestamp()),
    }
    token = jwt.encode(payload, _jwt_secret(connection_string), algorithm="HS256")
    manager = _get_cookie_manager()
    manager.set(_COOKIE_NAME, token, expires_at=login_time + SESSION_LIFETIME)


def clear_session_cookie() -> None:
    manager = _get_cookie_manager()
    manager.delete(_COOKIE_NAME)

def restore_session_from_cookie(connection_string: str) -> None:
    if st.session_state.get("user"):
        return

    manager = _get_cookie_manager()
    token: str | None = manager.get(_COOKIE_NAME)
    if not token:
        return

    try:
        payload = jwt.decode(token, _jwt_secret(connection_string), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        clear_session_cookie()
        return
    except jwt.InvalidTokenError:
        clear_session_cookie()
        return

    username: str = payload["sub"]
    user = get_user(connection_string, username)
    if user is None:
        clear_session_cookie()
        return

    st.session_state.user = user
    st.session_state.login_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    conversation_history(connection_string)
