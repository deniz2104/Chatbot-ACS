from datetime import datetime
from zoneinfo import ZoneInfo
from collections.abc import Callable
import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh

from src.UI.constants import _CLEAR_DELAY

_RO_TZ = ZoneInfo("Europe/Bucharest")

def _render_field_requirements(element: str, requirements: list[tuple[str, Callable]], render: bool = True) -> bool:
    if not element:
        if render and element != "":
            for label, _ in requirements:
                st.markdown(f":red[❌ {label}]")
        return False
    passed = True
    for label, check in requirements:
        met = check(element)
        if render:
            icon, color = ("✅", "green") if met else ("❌", "red")
            st.markdown(f":{color}[{icon} {label}]")
        passed &= met
    return passed

def elapsed(key: str) -> float:
    since = st.session_state.get(key)
    return time.time() - since if since else 0.0

def format_date(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string).astimezone(_RO_TZ)
        return dt.strftime("%d %b %Y, %H:%M")
    except (ValueError, TypeError):
        return ""

def timing_placeholder(placeholder, key: str, field: str, field_request: list[tuple[str, Callable]], delay: int = 1) -> bool:
    if elapsed(key) < delay:
        with placeholder.container():
            return _render_field_requirements(field, field_request)
    else:
        placeholder.empty()
        return _render_field_requirements(field, field_request, render=False)

def navigate_to(page: str) -> None:
    st.session_state.auth_page = page
    st.rerun()


def autorefresh_if_validating(keys: list[str], now: float) -> None:
    if any(st.session_state.get(k) and now - st.session_state[k] < _CLEAR_DELAY for k in keys):
        st_autorefresh(interval=500, key="req_autorefresh")


def send_otp(username: str, email: str, reason: str = "verification") -> bool:
    from src.azure.acs.email_sender import send_otp_email
    try:
        send_otp_email(username, email, reason=reason)
        return True
    except Exception as e:
        st.exception(e)
        return False


def validate_field(is_valid: bool, key: str, message: str, curr_moment: float) -> None:
    if not is_valid:
        st.session_state.pop(key, None)
        st.info(message)
    elif key not in st.session_state:
        st.session_state[key] = curr_moment
