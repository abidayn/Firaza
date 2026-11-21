"""Vector store: ChromaDB, with an in-memory NumPy fallback.

ChromaDB is the vector database used in deployment (Linux). On the development
machine Windows' Application Control policy blocks one of chromadb's native DLLs,
so `get_store()` falls back to a small NumPy cosine-similarity index with the same
interface. `backend_name` tells which one is active (shown in /health).
"""
from __future__ import annotations

import numpy as np


class NumpyStore:
    backend_name = "numpy-fallback"

    def __init__(self):
        self.ids: list[str] = []
        self.docs: list[str] = []
        self.metas: list[dict] = []
        self.vecs = np.zeros((0, 0), dtype=np.float32)

    def count(self) -> int:
        return len(self.ids)

    def reset(self) -> None:
        self.__init__()

    def add(self, ids, embeddings, documents, metadatas) -> None:
        v = np.asarray(embeddings, dtype=np.float32)
        v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
        self.vecs = v if self.vecs.size == 0 else np.vstack([self.vecs, v])
        self.ids += list(ids)
        self.docs += list(documents)
        self.metas += list(metadatas)

    def _match(self, where: dict | None) -> list[int]:
        where = where or {}
        return [i for i, m in enumerate(self.metas) if all(m.get(k) == v for k, v in where.items())]

    def get(self, where: dict) -> list[dict]:
        return [{"id": self.ids[i], "text": self.docs[i], "meta": self.metas[i]} for i in self._match(where)]

    def query(self, embedding, n: int, where: dict | None = None) -> list[dict]:
        idx = self._match(where)
        if not idx:
            return []
        q = np.asarray(embedding, dtype=np.float32)
        q /= np.linalg.norm(q) + 1e-12
        sims = self.vecs[idx] @ q
        order = np.argsort(-sims)[:n]
        return [{"id": self.ids[idx[j]], "text": self.docs[idx[j]], "meta": self.metas[idx[j]],
                 "score": float(sims[j])} for j in order]


class ChromaStore:
    backend_name = "chromadb"

    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        self._client = chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))
        self._make()

    def _make(self):
        self.col = self._client.get_or_create_collection("firaza_kb", metadata={"hnsw:space": "cosine"})

    def count(self) -> int:
        return self.col.count()

    def reset(self) -> None:
        self._client.delete_collection("firaza_kb")
        self._make()

    def add(self, ids, embeddings, documents, metadatas) -> None:
        self.col.add(ids=list(ids), embeddings=[list(map(float, e)) for e in embeddings],
                     documents=list(documents), metadatas=list(metadatas))

    def get(self, where: dict) -> list[dict]:
        r = self.col.get(where=where)
        return [{"id": i, "text": d, "meta": m} for i, d, m in zip(r["ids"], r["documents"], r["metadatas"])]

    def query(self, embedding, n: int, where: dict | None = None) -> list[dict]:
        r = self.col.query(query_embeddings=[list(map(float, embedding))], n_results=n, where=where)
        return [{"id": i, "text": d, "meta": m, "score": 1 - dist}
                for i, d, m, dist in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])]


_store = None


def get_store():
    global _store
    if _store is None:
        try:
            _store = ChromaStore()
        except Exception:
            _store = NumpyStore()
    return _store
