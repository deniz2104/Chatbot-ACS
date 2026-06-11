import streamlit as st

from sandbox.delete_chatbot_session import delete_session
from sandbox.conversation_context import save_conversation_context
from sandbox.load_conversations import load_conversation_history, switch_conversation
from sandbox.show_sources_data import render_sources


def _render_sidebar() -> None:
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            transform: translateZ(0) !important;
        }
        section[data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 15rem !important;
            max-width: 15rem !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            min-width: 0 !important;
            width: 0 !important;
            overflow: hidden !important;
        }
        div.element-container:has(#sidebar-spacer) + div.element-container {
            position: fixed !important;
            bottom: 0rem !important;
            left: 0rem !important;
            right: 0rem !important;
            z-index: 999 !important;
            background-color: var(--secondary-background-color) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Conversații")

        if st.button("＋ Conversație nouă", use_container_width=True):
            save_conversation_context()
            load_conversation_history()
            st.rerun()

        st.divider()

        for conversation in st.session_state.past_conversations:
            is_active = conversation["RowKey"] == st.session_state.conversation_id
            label = conversation.get("title") or "Conversație nouă"
            date = conversation.get("last_active", "")
            button_label = f"{'▶ ' if is_active else ''}{label}\n{date}"
            if st.button(button_label, key=conversation["RowKey"], use_container_width=True, disabled=is_active):
                save_conversation_context()
                switch_conversation(conversation["RowKey"])
                st.rerun()

        st.markdown('<div id="sidebar-spacer"></div>', unsafe_allow_html=True)

        if st.button("Logout", on_click=delete_session):
            st.rerun()


def render_chatbot() -> None:
    _render_sidebar()

    st.title("Chatbot ACS")

    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    render_sources()

    if prompt := st.chat_input("Întreabă ceva despre facultate..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        response = "[Sandbox] Backend not connected. This is a placeholder response."

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
