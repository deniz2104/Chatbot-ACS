from datetime import datetime

import streamlit as st
import time


def elapsed(key: str) -> float:
    since = st.session_state.get(key)
    return time.time() - since if since else 0.0

def format_date(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d %b %Y")
    except (ValueError, TypeError):
        return ""
