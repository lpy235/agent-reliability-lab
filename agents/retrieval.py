from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def load_documents(docs_dir: str | Path) -> list[dict[str, str]]:
    root = Path(docs_dir)
    if not root.exists():
        raise FileNotFoundError(f"Docs directory not found: {root}")

    docs = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        docs.append({"source": str(path), "text": path.read_text(encoding="utf-8")})

    if not docs:
        raise ValueError(f"No markdown or text documents found in {root}")
    return docs


def split_document(source: str, text: str) -> list[dict[str, Any]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    return [
        {"chunk_id": f"{Path(source).name}#{index}", "source": source, "text": block}
        for index, block in enumerate(blocks)
    ]


def retrieve_chunks(question: str, docs_dir: str | Path, top_k: int = 3) -> list[dict[str, Any]]:
    question_tokens = tokenize(question)
    chunks: list[dict[str, Any]] = []
    for doc in load_documents(docs_dir):
        chunks.extend(split_document(doc["source"], doc["text"]))

    scored = []
    for index, chunk in enumerate(chunks):
        overlap = len(question_tokens & tokenize(chunk["text"]))
        scored.append((overlap, -index, chunk))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    positive = [chunk for score, _, chunk in scored[:top_k] if score > 0]
    return positive or [chunk for _, _, chunk in scored[:top_k]]
