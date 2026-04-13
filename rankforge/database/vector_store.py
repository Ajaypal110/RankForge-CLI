"""
RankForge CLI - Vector Store
==============================
Optional vector memory using ChromaDB for semantic search over stored results.
Falls back to simple JSON keyword search if ChromaDB is not installed.
"""

import json
from pathlib import Path
from typing import Any, Optional

from rankforge.config.settings import settings
from rankforge.utils.logger import get_logger

logger = get_logger("rankforge.vector_store")

# Try importing ChromaDB (optional dependency)
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorStore:
    """
    Semantic search over stored SEO data.

    Uses ChromaDB when available; falls back to naive keyword search
    over a flat JSON index.
    """

    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.store_dir = Path(settings.data_dir) / project_name / "vectors"
        self.store_dir.mkdir(parents=True, exist_ok=True)

        if CHROMA_AVAILABLE:
            self._init_chroma()
        else:
            logger.info("ChromaDB not installed -- using JSON keyword fallback.")
            self.fallback_file = self.store_dir / "index.json"
            self._fallback_data: list[dict] = self._load_fallback()

    # ── ChromaDB Backend ─────────────────────────────────────────────

    def _init_chroma(self) -> None:
        """Initialise a persistent ChromaDB client."""
        self.client = chromadb.Client(
            ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.store_dir),
                anonymized_telemetry=False,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=f"rankforge_{self.project_name}"
        )
        logger.debug("ChromaDB collection ready: %s", self.collection.name)

    # ── Fallback Backend ─────────────────────────────────────────────

    def _load_fallback(self) -> list[dict]:
        if self.fallback_file.exists():
            try:
                return json.loads(self.fallback_file.read_text("utf-8"))
            except Exception:
                return []
        return []

    def _save_fallback(self) -> None:
        self.fallback_file.write_text(
            json.dumps(self._fallback_data, indent=2, default=str), encoding="utf-8"
        )

    # ── Public API ───────────────────────────────────────────────────

    def add(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        """Add a document to the vector store."""
        meta = metadata or {}

        if CHROMA_AVAILABLE:
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[meta],
            )
        else:
            self._fallback_data.append(
                {"id": doc_id, "text": text, "metadata": meta}
            )
            self._save_fallback()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Search for relevant documents.

        Returns list of dicts with keys: id, text, score (if available).
        """
        if CHROMA_AVAILABLE:
            results = self.collection.query(query_texts=[query], n_results=top_k)
            docs = []
            for i, doc_id in enumerate(results["ids"][0]):
                docs.append(
                    {
                        "id": doc_id,
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    }
                )
            return docs
        else:
            # Naive keyword search fallback
            query_lower = query.lower()
            scored = []
            for entry in self._fallback_data:
                text_lower = entry["text"].lower()
                # Simple relevance: count query-word occurrences
                score = sum(1 for w in query_lower.split() if w in text_lower)
                if score > 0:
                    scored.append({**entry, "score": score})
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]
