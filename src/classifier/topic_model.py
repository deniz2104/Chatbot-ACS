import json
import os

from bertopic import BERTopic
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = os.environ.get("SCRAPY_OUTPUT_PATH", "src/spider/output.json")
OUTPUT_PATH = os.environ.get("CLASSIFIER_OUTPUT_PATH", "src/classifier/classified.json")
MODEL_PATH = os.environ.get("CLASSIFIER_MODEL_PATH", "src/classifier/model")


def load_documents(path: str) -> tuple[list[str], list[dict]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []
    entries = []
    for entry in data:
        content = entry.get("content", "")
        if content:
            documents.append(content)
            entries.append(entry)

    return documents, entries


def classify(documents: list[str], entries: list[dict]) -> list[dict]:
    topic_model = BERTopic(language="multilingual", min_topic_size=3)
    topics, probs = topic_model.fit_transform(documents)

    for entry, topic_id, prob in zip(entries, topics, probs):
        keywords = topic_model.get_topic(topic_id)
        entry["category_id"] = topic_id
        entry["keywords"] = [word for word, _ in keywords] if topic_id != -1 else []
        entry["confidence"] = float(prob.max())

    topic_model.save(MODEL_PATH)
    return entries


def save_results(entries: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def main() -> None:
    print(f"Loading documents from {INPUT_PATH}...")
    documents, entries = load_documents(INPUT_PATH)
    print(f"Loaded {len(documents)} documents with content")

    print("Running BERTopic...")
    results = classify(documents, entries)

    save_results(results, OUTPUT_PATH)
    print(f"Saved {len(results)} classified entries to {OUTPUT_PATH}")

    category_ids = {e["category_id"] for e in results}
    print(f"Discovered {len(category_ids)} categories (including outliers as -1)")


if __name__ == "__main__":
    main()