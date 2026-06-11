import streamlit as st
from collections.abc import Callable


def meeting_request(element: str, requirements: list[tuple[str, Callable]], render: bool = True) -> bool:
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
