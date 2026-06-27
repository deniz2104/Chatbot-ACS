"""
Test pipeline script — runs all 65 evaluation questions through the full
query pipeline and writes system responses to evaluare.csv.

Usage:
    uv run python test_pipeline.py
"""

import csv
import sys
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Patch non-LLM Azure KV secrets so we don't need Redis / storage / etc.
# get_llm_api_key is left unpatched — it fetches from Azure KV directly.
# ---------------------------------------------------------------------------
_kv_patches = {
    "src.azure.kv.get_secrets_from_kv.get_redis_url": lambda: None,
    "src.azure.kv.get_secrets_from_kv.get_file_store": lambda: "/tmp/scrapy_files",
    "src.azure.kv.get_secrets_from_kv.get_storage_account_secret": lambda: "",
}

_patch_objects = [patch(k, v) for k, v in _kv_patches.items()]
for p in _patch_objects:
    p.start()

# ---------------------------------------------------------------------------
# Project imports (after patching)
# ---------------------------------------------------------------------------
from src.ai_prompts.query_rewriter import rewrite_query
from src.vector_database.query import query as handle_query, initialize_query
from src.ai_prompts.chatbot_responder import get_chatbot_response

CSV_PATH = "evaluare.csv"

# ---------------------------------------------------------------------------
# Conversation history for follow-up questions (56-60).
# Keys are question numbers; values are the prior turns needed.
# These will be populated from the responses of the referenced questions
# during the run, so order matters: referenced questions run first.
# ---------------------------------------------------------------------------
FOLLOWUP_REFS = {
    56: 1,   # "Câte credite are?" -> after Q1 (cine predă BD)
    57: 2,   # "Cine o predă?"     -> after Q2 (titular SO)
    58: 31,  # "Când se termină?"  -> after Q31 (sesiunea de iarnă)
    59: 21,  # "Ce documente?"     -> after Q21 (cerere reexaminare)
    60: 1,   # "Are pagină web?"   -> after Q1 (titular curs)
}

# Actual follow-up question text (without the [Urmărire ...] prefix)
FOLLOWUP_QUESTIONS = {
    56: "Câte credite are?",
    57: "Cine o predă?",
    58: "Când se termină?",
    59: "Ce documente sunt necesare?",
    60: "Are pagină web?",
}


def log(msg: str) -> None:
    print(msg, flush=True)


def collect_stream(generator) -> str:
    return "".join(generator)


def run_question(question: str, history: list[dict]) -> str:
    resolved = rewrite_query(question, history=history if history else None)
    docs = handle_query(resolved, user_context="")
    stream = get_chatbot_response(
        user_query=question,
        docs=docs,
        history=history,
        user_context="",
        conversation_summary="",
    )
    return collect_stream(stream)


def main():
    log("Initialising reranker model (first run may take a moment)...")
    initialize_query()
    log("Model ready.\n")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = ["nr", "intrebare", "raspuns_sistem", "verdict"]
    responses: dict[int, str] = {}

    total = len(rows)
    for i, row in enumerate(rows, 1):
        nr = int(row["nr"])
        is_followup = nr in FOLLOWUP_REFS

        if is_followup:
            ref_nr = FOLLOWUP_REFS[nr]
            prior_q = next(r["intrebare"] for r in rows if int(r["nr"]) == ref_nr)
            prior_a = responses.get(ref_nr, "")
            history = [
                {"role": "user",      "content": prior_q},
                {"role": "assistant", "content": prior_a},
            ]
            question = FOLLOWUP_QUESTIONS[nr]
        else:
            history = []
            question = row["intrebare"]

        log(f"[{i}/{total}] Q{nr}: {question[:80]}")
        try:
            answer = run_question(question, history)
            log(f"  OK -> {answer[:120]}\n")
        except Exception as e:
            answer = f"[EROARE: {e}]"
            log(f"  ERROR: {e}\n")

        responses[nr] = answer
        row["raspuns_sistem"] = answer

        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        log(f"  Saved to CSV.")

    log(f"\nDone. All {total} answers written to {CSV_PATH}")

    for p in _patch_objects:
        p.stop()


if __name__ == "__main__":
    main()
