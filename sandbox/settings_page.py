import streamlit as st
from sandbox.delete_chatbot_session import delete_session

def render_settings() -> None:
    st.markdown("""
        <style>
        div.element-container:has(#logout-btn-anchor) + div.element-container {
            position: fixed !important;
            bottom: 2rem !important;
            left: 2rem !important;
            width: 14rem !important;
            z-index: 9999 !important;
        }
        div.element-container:has(#logout-btn-anchor) + div.element-container button {
            height: 3.5rem !important;
            font-size: 1.1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.button("← Back to Chat"):
        st.session_state.show_settings = False
        st.rerun()

    st.markdown('<div id="logout-btn-anchor"></div>', unsafe_allow_html=True)
    if st.button("Logout", on_click=delete_session):
        st.rerun()

    label = "Hide sources" if st.session_state.show_sources else "Show sources of data"
    if st.button(label):
        st.session_state.show_sources = not st.session_state.show_sources
        st.rerun()

    if st.session_state.show_sources:
        sources = st.session_state.get("last_sources", [])
        if not sources:
            st.info("No query has been made yet.")
        else:
            st.subheader("Sources used in last response")
            for s in sources:
                st.markdown(f"- [{s['title']}]({s['url']})")
