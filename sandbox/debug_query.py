"""
Full pipeline debug for a single query.

Instruments every stage: rewrite → keyword extraction → category scoring →
URL scoring → VDB candidate search → similarity filtering → reranking →
LLM response. Writes a structured debug report to sandbox/debug_output.json
and a human-readable summary to sandbox/debug_output.txt.

Usage:
    python -m sandbox.debug_query
    QUERY="..." python -m sandbox.debug_query
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s %(message)s")
for _mod in (
    "sentence_transformers", "chromadb", "azure", "azure.identity",
    "azure.core.pipeline.policies.http_logging_policy",
):
    logging.getLogger(_mod).setLevel(logging.ERROR)

from src.ai_prompts.chatbot_responder import get_chatbot_response
from src.ai_prompts.query_keywords_extractor import extract_keywords
from src.ai_prompts.query_rewriter import rewrite_query
from src.categorization.encoder import _encode_matrix
from src.chatbot.cache import _load_categories, _load_crawled_urls
from src.secrets.get_secrets_from_kv import general_file_store
from sentence_transformers import util


QUERY = os.environ.get("QUERY", "Cine e profesor la calculatoare in anul 3?")
OUT_DIR = Path(__file__).parent
OUT_JSON = OUT_DIR / "debug_output.json"
OUT_TXT = OUT_DIR / "debug_output.txt"


# ── instrumented helpers ──────────────────────────────────────────────────────

def _vdb_search(question: str, k: int):
    """Return (raw, filtered) candidate lists with cosine scores."""
    from src.vector_database.vector_db import search_all
    from src.vector_database.constants import _SIMILARITY_THRESHOLD

    raw = search_all(question, k=k)
    filtered = [(doc, s) for doc, s in raw if s >= _SIMILARITY_THRESHOLD]
    return raw, filtered


def _rerank(question: str, candidates: list) -> list:
    """Return list of (doc, reranker_score), descending."""
    from src.vector_database.query import get_reranker
    from src.vector_database.constants import _RERANKER_TOP_N

    reranker = get_reranker()
    scores = reranker.predict([(question, doc.page_content) for doc in candidates])
    return sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)[:_RERANKER_TOP_N]


def _cat_score(query_emb, cat_emb) -> float:
    return float(util.cos_sim(query_emb, cat_emb).max(dim=1).values.mean())


async def _resolve_instrumented(query: str):
    """
    Full URL resolution with captured intermediate scores.

    Returns (keywords, category_scores, embedding_url_hits, lexical_url_hits, resolved_urls).
    """
    from src.chatbot.scoring import _CATEGORY_THRESHOLD, _URL_THRESHOLD, _TOP_CATEGORIES
    from src.chatbot.cache import _load_raw_urls

    files_store = general_file_store()
    keywords = extract_keywords(query, tokens=256)
    if not keywords:
        return keywords, [], [], [], set()

    categories = list(_load_categories(files_store))
    if not categories:
        return keywords, [], [], [], set()

    query_emb = await _encode_matrix(keywords)

    cat_scores_raw = [
        {
            "score": round(_cat_score(query_emb, cat_emb), 4),
            "sample_url": url_entries[0][0] if url_entries else "?",
            "url_count": len(url_entries),
        }
        for cat_emb, url_entries in categories
    ]

    top_cats = sorted(
        [
            (cat_emb, url_entries)
            for cat_emb, url_entries in categories
            if _cat_score(query_emb, cat_emb) >= _CATEGORY_THRESHOLD
        ],
        key=lambda x: _cat_score(query_emb, x[0]),
        reverse=True,
    )[:_TOP_CATEGORIES]

    embedding_hits: list[dict] = []
    seen: set[str] = set()
    for cat_emb, url_entries in top_cats:
        c_score = _cat_score(query_emb, cat_emb)
        for url, url_emb in url_entries:
            u_score = float(util.cos_sim(query_emb, url_emb).max(dim=1).values.mean())
            if u_score >= _URL_THRESHOLD:
                embedding_hits.append({
                    "url": url,
                    "url_score": round(u_score, 4),
                    "category_score": round(c_score, 4),
                    "source": "embedding",
                })
                seen.add(url)

    embedding_hits.sort(key=lambda x: x["url_score"], reverse=True)

    # Lexical pass — exact keyword match against scraped URL keyword lists
    kw_lower = {k.lower() for k in keywords}
    lexical_hits: list[dict] = []
    for entry in _load_raw_urls(files_store):
        entry_kws = {k.lower() for k in entry.get("keywords", [])}
        if kw_lower & entry_kws:
            matched_kws = sorted(kw_lower & entry_kws)
            lexical_hits.append({
                "url": entry["url"],
                "matched_keywords": matched_kws,
                "source": "lexical",
            })
            seen.add(entry["url"])

    return list(keywords), cat_scores_raw, embedding_hits, lexical_hits, seen


# ── main pipeline ─────────────────────────────────────────────────────────────

async def run_debug(question: str) -> dict:
    """Run the full chatbot pipeline and return a structured debug report."""
    from src.vector_database.constants import (
        _SIMILARITY_THRESHOLD, _CHUNKS_CHOSEN,
    )

    report: dict = {
        "query": {"original": question, "rewritten": None, "query_keywords": []},
        "url_resolution": {
            "category_scores_all": [],
            "embedding_url_hits": [],
            "lexical_url_hits": [],
            "resolved_urls": [],
            "already_crawled": [],
            "uncrawled": [],
        },
        "vector_db": {
            "threshold": _SIMILARITY_THRESHOLD,
            "candidates_raw_count": 0,
            "candidates_filtered_count": 0,
            "candidates_raw": [],
            "candidates_filtered": [],
            "reranked": [],
        },
        "llm_response": None,
        "timings_ms": {},
    }

    # 1. Rewrite
    print(f"\n[1/6] Rewriting query: '{question}'")
    t0 = time.perf_counter()
    rewritten = rewrite_query(question)
    report["query"]["rewritten"] = rewritten
    report["timings_ms"]["rewrite"] = round((time.perf_counter() - t0) * 1000, 1)
    print(f"      -> '{rewritten}'")

    # 2. Keyword extraction + URL resolution
    print("[2/6] Extracting keywords & resolving URLs...")
    t0 = time.perf_counter()
    keywords, cat_scores, emb_hits, lex_hits, resolved_urls = await _resolve_instrumented(rewritten)
    report["timings_ms"]["resolve_urls_total"] = round((time.perf_counter() - t0) * 1000, 1)

    report["query"]["query_keywords"] = sorted(keywords)
    report["url_resolution"]["category_scores_all"] = sorted(
        cat_scores, key=lambda x: x["score"], reverse=True
    )
    report["url_resolution"]["embedding_url_hits"] = emb_hits
    report["url_resolution"]["lexical_url_hits"] = lex_hits
    report["url_resolution"]["resolved_urls"] = sorted(resolved_urls)
    print(f"      -> {len(keywords)} keywords: {sorted(keywords)}")
    print(f"      -> {len(emb_hits)} embedding hits, {len(lex_hits)} lexical hits")
    print(f"      -> {len(resolved_urls)} total URLs resolved")

    # 3. Crawled-URL cache check
    print("[3/6] Checking crawled-URLs cache...")
    try:
        already_crawled = _load_crawled_urls()
        uncrawled = sorted(u for u in resolved_urls if u not in already_crawled)
        report["url_resolution"]["already_crawled"] = sorted(already_crawled & resolved_urls)
        report["url_resolution"]["uncrawled"] = uncrawled
        n_already = len(already_crawled & resolved_urls)
        print(f"      -> {n_already} already crawled, {len(uncrawled)} new")
    except FileNotFoundError:
        report["url_resolution"]["uncrawled"] = sorted(resolved_urls)
        print("      -> crawled-URLs cache not found, treating all as new")

    # 4. VDB search
    print("[4/6] Searching vector DB...")
    t0 = time.perf_counter()
    raw_cands, filtered_cands = _vdb_search(rewritten, k=_CHUNKS_CHOSEN)
    report["timings_ms"]["vdb_search"] = round((time.perf_counter() - t0) * 1000, 1)

    report["vector_db"]["candidates_raw_count"] = len(raw_cands)
    report["vector_db"]["candidates_filtered_count"] = len(filtered_cands)
    report["vector_db"]["candidates_raw"] = [
        {
            "url": doc.metadata.get("url", ""),
            "similarity_score": round(float(s), 4),
            "content_preview": doc.page_content[:200],
            "metadata": {k: v for k, v in doc.metadata.items() if k != "content"},
        }
        for doc, s in sorted(raw_cands, key=lambda x: x[1], reverse=True)
    ]
    report["vector_db"]["candidates_filtered"] = [
        {
            "url": doc.metadata.get("url", ""),
            "similarity_score": round(float(s), 4),
            "content_preview": doc.page_content[:200],
        }
        for doc, s in sorted(filtered_cands, key=lambda x: x[1], reverse=True)
    ]
    print(
        f"      -> {len(raw_cands)} raw, "
        f"{len(filtered_cands)} above threshold={_SIMILARITY_THRESHOLD}"
    )

    # 5. Reranking
    print("[5/6] Reranking candidates...")
    docs_filtered = [doc for doc, _ in filtered_cands]
    if docs_filtered:
        t0 = time.perf_counter()
        reranked = _rerank(rewritten, docs_filtered)
        report["timings_ms"]["rerank"] = round((time.perf_counter() - t0) * 1000, 1)
        report["vector_db"]["reranked"] = [
            {
                "rank": i + 1,
                "url": doc.metadata.get("url", ""),
                "reranker_score": round(float(s), 4),
                "content_preview": doc.page_content[:300],
                "metadata": {k: v for k, v in doc.metadata.items() if k != "content"},
            }
            for i, (doc, s) in enumerate(reranked)
        ]
        final_docs = [doc for doc, _ in reranked]
        print(f"      -> top {len(reranked)} after reranking")
    else:
        final_docs = []
        print("      -> no candidates to rerank")

    # 6. LLM response
    print("[6/6] Getting LLM response...")
    t0 = time.perf_counter()
    response = get_chatbot_response(question, final_docs, [])
    report["timings_ms"]["llm_response"] = round((time.perf_counter() - t0) * 1000, 1)
    report["llm_response"] = response
    print(f"      -> response received ({len(response)} chars)")

    return report


# ── text report writer ────────────────────────────────────────────────────────

def _write_txt(report: dict, path: Path) -> None:
    sep = "=" * 80
    lines = [sep, "  ACS CHATBOT -- FULL PIPELINE DEBUG REPORT", sep, ""]

    q = report["query"]
    kw_str = ", ".join(q["query_keywords"]) if q["query_keywords"] else "(none)"
    lines += [
        "QUERY",
        f"  Original  : {q['original']}",
        f"  Rewritten : {q['rewritten']}",
        f"  Keywords  : {kw_str}",
        "",
        "TIMINGS (ms)",
    ]
    for k, v in report["timings_ms"].items():
        lines.append(f"  {k:<30} {v} ms")
    lines.append("")

    ur = report["url_resolution"]
    from src.chatbot.scoring import _CATEGORY_THRESHOLD, _URL_THRESHOLD
    lines += [
        "URL RESOLUTION",
        f"  Category threshold : {_CATEGORY_THRESHOLD}",
        f"  URL threshold      : {_URL_THRESHOLD}",
        f"  Categories scanned : {len(ur['category_scores_all'])}",
        f"  URLs resolved      : {len(ur['resolved_urls'])}",
        f"  Already crawled    : {len(ur['already_crawled'])}",
        f"  Uncrawled (new)    : {len(ur['uncrawled'])}",
        "",
        f"  Top category scores (above {_CATEGORY_THRESHOLD}):",
    ]
    above_cats = [c for c in ur["category_scores_all"] if c["score"] >= _CATEGORY_THRESHOLD]
    for c in above_cats[:10]:
        lines.append(
            f"    score={c['score']:.4f}  urls={c['url_count']}  sample={c['sample_url']}"
        )
    if not above_cats:
        lines.append("    (none above threshold)")
    lines.append("")

    lines.append("  Embedding URL hits (sorted by score):")
    for h in ur["embedding_url_hits"][:20]:
        lines.append(
            f"    url_score={h['url_score']:.4f}"
            f"  cat_score={h['category_score']:.4f}"
            f"  {h['url']}"
        )
    if not ur["embedding_url_hits"]:
        lines.append("    (none)")
    lines.append("")

    lines.append("  Lexical URL hits (verbatim keyword match):")
    for h in ur["lexical_url_hits"]:
        lines.append(f"    matched={h['matched_keywords']}  {h['url']}")
    if not ur["lexical_url_hits"]:
        lines.append("    (none)")
    lines.append("")

    vdb = report["vector_db"]
    lines += [
        "VECTOR DB",
        f"  Similarity threshold : {vdb['threshold']}",
        f"  Raw candidates       : {vdb['candidates_raw_count']}",
        f"  Above threshold      : {vdb['candidates_filtered_count']}",
        "",
        "  Raw candidates (sorted by similarity):",
    ]
    for c in vdb["candidates_raw"][:30]:
        lines.append(f"    sim={c['similarity_score']:.4f}  {c['url']}")
        lines.append(f"      preview: {c['content_preview'][:120]!r}")
    if not vdb["candidates_raw"]:
        lines.append("    (none)")
    lines.append("")

    lines.append("  Reranked top results:")
    for r in vdb["reranked"]:
        lines.append(
            f"    #{r['rank']}  reranker={r['reranker_score']:.4f}  {r['url']}"
        )
        lines.append(f"      preview: {r['content_preview'][:150]!r}")
    if not vdb["reranked"]:
        lines.append("    (none)")
    lines.append("")

    lines += [
        "LLM RESPONSE",
        "-" * 60,
        report["llm_response"] or "(no response)",
        "-" * 60,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print(f"\n{'='*60}")
    print(f"  DEBUG RUN -- query: '{QUERY}'")
    print("=" * 60)

    report = asyncio.run(run_debug(QUERY))

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_txt(report, OUT_TXT)

    print(f"\nDebug files written:")
    print(f"  JSON : {OUT_JSON}")
    print(f"  TXT  : {OUT_TXT}")

    print(f"\n{'─'*60}")
    print("SUMMARY")
    print("─" * 60)
    print(f"  Original query  : {report['query']['original']}")
    print(f"  Rewritten       : {report['query']['rewritten']}")
    kw = report["query"]["query_keywords"]
    print(f"  Keywords ({len(kw)})   : {', '.join(kw)}")
    print(f"  URLs resolved   : {len(report['url_resolution']['resolved_urls'])}")
    print(f"  VDB raw hits    : {report['vector_db']['candidates_raw_count']}")
    print(f"  VDB filtered    : {report['vector_db']['candidates_filtered_count']}")
    print(f"  Reranked top    : {len(report['vector_db']['reranked'])}")
    print("\n  Top reranked URLs:")
    for r in report["vector_db"]["reranked"]:
        print(f"    #{r['rank']}  score={r['reranker_score']:.4f}  {r['url']}")
    print("\n  Top embedding URL hits (by cosine sim):")
    for h in report["url_resolution"]["embedding_url_hits"][:5]:
        print(f"    url_score={h['url_score']:.4f}  cat={h['category_score']:.4f}  {h['url']}")
    print("\n  Lexical URL hits:")
    for h in report["url_resolution"]["lexical_url_hits"]:
        print(f"    matched={h['matched_keywords']}  {h['url']}")
    print(f"\n  Timings: { {k: str(v)+'ms' for k, v in report['timings_ms'].items()} }")
    print("\n  LLM Response:\n")
    print(f"  {report['llm_response']}")
    print()


if __name__ == "__main__":
    main()
