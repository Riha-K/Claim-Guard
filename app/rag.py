from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import settings

_model: SentenceTransformer | None = None


def _embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class PolicyStore:
    def __init__(self) -> None:
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection("claimguard_policies")

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        try:
            self.client.delete_collection("claimguard_policies")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection("claimguard_policies")

    def ingest(self, clear: bool = False) -> dict:
        if clear:
            self.clear()
        paths = sorted(settings.knowledge_base_dir.glob("*.md"))
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        for path in paths:
            raw = path.read_text(encoding="utf-8")
            for i, piece in enumerate(
                chunk_text(raw, settings.chunk_size, settings.chunk_overlap)
            ):
                digest = hashlib.sha1(f"{path.name}:{i}:{piece[:40]}".encode()).hexdigest()
                ids.append(digest)
                documents.append(piece)
                metadatas.append({"source": path.name, "chunk": i})
        if not documents:
            return {"files": 0, "chunks": 0}
        embeddings = _embedder().encode(documents, normalize_embeddings=True).tolist()
        self.collection.upsert(
            ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings
        )
        return {"files": len(paths), "chunks": len(documents)}

    def ensure(self) -> dict:
        if self.count() == 0:
            return self.ingest(clear=False)
        return {"files": None, "chunks": self.count(), "skipped": True}

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        self.ensure()
        k = top_k or settings.top_k
        emb = _embedder().encode([query], normalize_embeddings=True).tolist()
        result = self.collection.query(query_embeddings=emb, n_results=k)
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        out: list[RetrievedChunk] = []
        for text, meta, dist in zip(docs, metas, dists):
            score = 1.0 - float(dist) if dist is not None else 0.0
            out.append(
                RetrievedChunk(
                    text=text,
                    source=str((meta or {}).get("source", "unknown")),
                    score=score,
                )
            )
        return out
