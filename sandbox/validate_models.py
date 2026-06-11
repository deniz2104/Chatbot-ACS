import sys
sys.path.insert(0, ".")

def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    return condition

ok = True

print("\n=== Embed model ===")
from src.vector_database.vector_db import  _get_embeddings

embeddings = _get_embeddings()

ok &= check("Embeddings object loaded", embeddings is not None)

try:
    result = embeddings.embed_query("test sentence")
    ok &= check(f"Inference produces vector of length {len(result)}", len(result) > 0)
except Exception as e:
    ok &= check(f"Inference failed: {e}", False)

print("\n=== Reranker model ===")
from src.vector_database.query import _download_reranker, _get_reranker

if not _RERANKER_MODEL_PATH.exists():
    print(f"  Downloading {_RERANKER_MODEL} ...")
    _download_reranker()

ok &= check(f"Path exists: {_RERANKER_MODEL_PATH}", _RERANKER_MODEL_PATH.exists())

reranker = _get_reranker()
ok &= check("Reranker object loaded", reranker is not None)

try:
    scores = reranker.predict([("what is AI?", "Artificial intelligence is the simulation of human intelligence.")])
    ok &= check(f"Inference produces score: {scores[0]:.4f}", scores is not None)
except Exception as e:
    ok &= check(f"Inference failed: {e}", False)

print(f"\n{'All checks passed.' if ok else 'Some checks FAILED.'}")
sys.exit(0 if ok else 1)
