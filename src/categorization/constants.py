from sentence_transformers import SentenceTransformer

_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L6-v2")
_SIMILARITY_THRESHOLD = 0.60
