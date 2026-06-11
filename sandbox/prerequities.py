import streamlit as st
from sandbox.constants import DARK_THEME, DARK_BUTTON


def set_initial_prerequities():
    st.set_page_config(
        page_title="Chatbot ACS",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(f"{DARK_THEME + DARK_BUTTON}", unsafe_allow_html=True)
