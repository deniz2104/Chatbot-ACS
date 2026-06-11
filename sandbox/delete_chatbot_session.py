import streamlit as st


def delete_session() -> None:
    st.session_state.clear()
