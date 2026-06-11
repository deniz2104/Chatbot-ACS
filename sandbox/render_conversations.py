import streamlit as st
from sandbox.utils import format_date
from sandbox.conversation_context import save_conversation_context
from sandbox.conversation import conversation_history, load_conversation_messages


def render_past_conversations() -> None:
    conversations: list[dict] = st.session_state.get("conversations", [])

    if not conversations:
        st.caption("Nu există conversații anterioare.")
        return

    active_id = st.session_state.get("conversation_id")

    for conv in conversations:
        conv_id = conv.get("RowKey", "")
        title = conv.get("title", "Fără titlu")
        date_str = format_date(conv.get("created_at", ""))
        label = f"{title}\n{date_str}" if date_str else title
        is_active = conv_id == active_id

        if st.button(
            label,
            key=f"conv_{conv_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            save_conversation_context()
            st.session_state.conversation_id = conv_id
            st.session_state.messages = load_conversation_messages(conv_id)
            st.session_state.loaded_conversation_id = conv_id
            st.rerun()
