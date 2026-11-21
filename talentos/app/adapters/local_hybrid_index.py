from __future__ import annotations

import json
import math
import re
import threading
from collections import Counter
from pathlib import Path
from typing import Any

from app.domain.models import SearchHit
from app.ports.vector_index import VectorIndexPort

STOPWORDS = frozenset(
    {"a", "an", "and", "the", "in", "on", "of", "for", "to", "with", "at", "by", "is", "was"}
)


def _tokens(text: str) -> list[str]:
    tokens = [token.strip(".") for token in re.findall(r"[a-z0-9+#.]+", text.lower())]
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def _vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    counts = Counter(tokens)
    return {token: count * idf.get(token, 1.0) for token, count in counts.items()}


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left) & set(right)
    dot = sum(left[key] * right[key] for key in shared)
    norm_left = math.sqrt(sum(value * value for value in left.values()))
    norm_right = math.sqrt(sum(value * value for value in right.values()))
    return dot / (norm_left * norm_right) if norm_left and norm_right else 0.0


def _matches(metadata: dict[str, object], filters: dict[str, object] | None) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        actual = metadata.get(key)
        if isinstance(actual, list):
            if expected not in actual:
                return False
        elif actual != expected:
            return False
    return True


class LocalHybridIndex(VectorIndexPort):
    """TF-IDF cosine search with metadata filtering, persisted to a local JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._docs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            return
        try:
            loaded = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(loaded, dict):
            self._docs = dict(loaded)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(self._path.suffix + ".tmp")
        temporary.write_text(json.dumps(self._docs), encoding="utf-8")
        temporary.replace(self._path)

    def upsert(
        self, doc_id: str, tenant_id: str, text: str, metadata: dict[str, object]
    ) -> None:
        with self._lock:
            self._docs[doc_id] = {
                "tenant_id": tenant_id,
                "text": text,
                "metadata": metadata,
            }
            self._save()

    def search(
        self,
        tenant_id: str,
        query: str,
        *,
        top_k: int = 10,
        metadata_filter: dict[str, object] | None = None,
    ) -> list[SearchHit]:
        with self._lock:
            candidates = [
                (doc_id, doc)
                for doc_id, doc in self._docs.items()
                if doc["tenant_id"] == tenant_id
                and _matches(doc["metadata"], metadata_filter)
            ]
            if not candidates:
                return []

            tokenized = {doc_id: _tokens(str(doc["text"])) for doc_id, doc in candidates}
            frequencies: Counter[str] = Counter()
            for tokens in tokenized.values():
                frequencies.update(set(tokens))
            total = len(candidates)
            idf = {
                token: math.log((1 + total) / (1 + count)) + 1.0
                for token, count in frequencies.items()
            }

            query_vector = _vector(_tokens(query), idf)
            hits: list[SearchHit] = []
            for doc_id, tokens in tokenized.items():
                score = _cosine(query_vector, _vector(tokens, idf))
                if score > 0.0:
                    hits.append(
                        SearchHit(
                            doc_id=doc_id,
                            score=score,
                            metadata=dict(self._docs[doc_id]["metadata"]),
                        )
                    )
            hits.sort(key=lambda hit: (-hit.score, hit.doc_id))
            return hits[:top_k]
