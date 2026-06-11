import uuid
from datetime import datetime, timezone

import streamlit as st

_MOCK_CONVERSATIONS = [
    {
        "RowKey": "mock-conv-1",
        "title": "Orar semestrul I",
        "created_at": "2025-10-01T10:00:00",
    },
    {
        "RowKey": "mock-conv-2",
        "title": "Examene sesiune",
        "created_at": "2025-11-15T14:30:00",
    },
    {
        "RowKey": "mock-conv-3",
        "title": "Burse și taxe",
        "created_at": "2025-12-03T09:15:00",
    },
]

_MOCK_MESSAGES = {
    "mock-conv-1": [
        {"role": "user",      "content": "Care este orarul pentru luni?"},
        {"role": "assistant", "content": "Luni ai Matematică la 8:00, Fizică la 10:00 și Programare la 12:00."},
    ],
    "mock-conv-2": [
        {"role": "user",      "content": "Când începe sesiunea de iarnă?"},
        {"role": "assistant", "content": "Sesiunea de iarnă începe pe 20 ianuarie și durează până pe 10 februarie."},
    ],
    "mock-conv-3": [
        {"role": "user",      "content": "Cum pot aplica pentru bursă?"},
        {"role": "assistant", "content": "Poți aplica pentru bursă completând formularul de la secretariat până pe 30 septembrie."},
    ],
}


def create_user_conversation() -> None:
    new_id = str(uuid.uuid4())
    st.session_state.conversation_id = new_id
    st.session_state.loaded_conversation_id = new_id
    st.session_state.messages = []
    new_conv = {
        "RowKey": new_id,
        "title": "Conversație nouă",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    st.session_state.conversations = [new_conv] + st.session_state.get("conversations", [])


def conversation_history() -> None:
    if not st.session_state.get("conversations"):
        st.session_state.conversations = list(_MOCK_CONVERSATIONS)


def load_conversation_messages(conversation_id: str) -> list[dict]:
    return list(_MOCK_MESSAGES.get(conversation_id, []))
