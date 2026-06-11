from datetime import datetime
from collections.abc import Callable
from src.UI.constants import _CLEAR_DELAY

import streamlit as st
import time

def _meeting_request(element: str, requirements: list[tuple[str, Callable]], render: bool = True) -> bool:
    if not element:
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
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d %b %Y")
    except (ValueError, TypeError):
        return ""

def timing_placeholder(placeholder, key: str, field: str, field_request: list[tuple[str, Callable]], delay: int = _CLEAR_DELAY) -> bool:
    if elapsed(key) < delay:
        with placeholder.container():
            return _meeting_request(field, field_request)
    else:
        placeholder.empty()
        return _meeting_request(field, field_request, render=False)

def validate_field(is_valid: bool, key: str, message: str, curr_moment: float) -> None:
    if not is_valid:
        st.session_state.pop(key, None)
        st.info(message)
    elif key not in st.session_state:
        st.session_state[key] = curr_moment
