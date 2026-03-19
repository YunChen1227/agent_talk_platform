"""
Concrete implementations of EmbeddingRepository.

  - ESEmbeddingRepository   → real Elasticsearch backend
  - JsonEmbeddingRepository → local JSON file backend (dev_1)
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from app.repositories.base import EmbeddingRepository

# ---------------------------------------------------------------------------
# Elasticsearch implementation
# ---------------------------------------------------------------------------

AGENT_EMBEDDING_INDEX = "agent_embeddings"
EMBEDDING_DIM = 1536


class ESEmbeddingRepository(EmbeddingRepository):

    def __init__(self, es_url: str):
        self._es_url = es_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            from elasticsearch import AsyncElasticsearch
            self._client = AsyncElasticsearch(hosts=[self._es_url])
        return self._client

    async def init(self) -> None:
        client = self._get_client()
        if await client.indices.exists(index=AGENT_EMBEDDING_INDEX):
            return
        await client.indices.create(
            index=AGENT_EMBEDDING_INDEX,
            settings={"number_of_shards": 1, "number_of_replicas": 0},
            mappings={
                "properties": {
                    "agent_id": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": EMBEDDING_DIM,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        )
        print(f"[es] Created index '{AGENT_EMBEDDING_INDEX}'")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def upsert(self, agent_id: str, embedding: List[float]) -> None:
        client = self._get_client()
        await client.index(
            index=AGENT_EMBEDDING_INDEX,
            id=agent_id,
            document={"agent_id": agent_id, "embedding": embedding},
            refresh="wait_for",
        )

    async def delete(self, agent_id: str) -> None:
        client = self._get_client()
        try:
            await client.delete(
                index=AGENT_EMBEDDING_INDEX, id=agent_id, refresh="wait_for"
            )
        except Exception:
            pass

    async def get(self, agent_id: str) -> Optional[List[float]]:
        client = self._get_client()
        try:
            doc = await client.get(index=AGENT_EMBEDDING_INDEX, id=agent_id)
            return doc["_source"]["embedding"]
        except Exception:
            return None

    async def search_nearest(
        self,
        embedding: List[float],
        k: int = 10,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        client = self._get_client()
        knn_query: Dict = {
            "field": "embedding",
            "query_vector": embedding,
            "k": k,
            "num_candidates": max(k * 4, 50),
        }
        if exclude_ids:
            knn_query["filter"] = {
                "bool": {"must_not": [{"ids": {"values": exclude_ids}}]}
            }
        resp = await client.search(
            index=AGENT_EMBEDDING_INDEX, knn=knn_query, size=k
        )
        return [
            {"agent_id": hit["_source"]["agent_id"], "score": hit["_score"]}
            for hit in resp["hits"]["hits"]
        ]


# ---------------------------------------------------------------------------
# JSON-file implementation (dev_1, no ES needed)
# ---------------------------------------------------------------------------


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class JsonEmbeddingRepository(EmbeddingRepository):

    def __init__(self, file_path: Path):
        self._file = file_path
        self._store: Dict[str, Dict] = {}

    def _load(self):
        if self._file.exists():
            with open(self._file, "r", encoding="utf-8") as f:
                self._store = json.load(f)
        else:
            self._store = {}

    def _save(self):
        self._file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._store, f, ensure_ascii=False)

    async def init(self) -> None:
        self._load()
        print(f"[es_json] Loaded {len(self._store)} embeddings from {self._file}")

    async def close(self) -> None:
        self._save()

    async def upsert(self, agent_id: str, embedding: List[float]) -> None:
        self._store[agent_id] = {"agent_id": agent_id, "embedding": embedding}
        self._save()

    async def delete(self, agent_id: str) -> None:
        self._store.pop(agent_id, None)
        self._save()

    async def get(self, agent_id: str) -> Optional[List[float]]:
        doc = self._store.get(agent_id)
        return doc["embedding"] if doc else None

    async def search_nearest(
        self,
        embedding: List[float],
        k: int = 10,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        exclude = set(exclude_ids or [])
        scored = []
        for aid, doc in self._store.items():
            if aid in exclude:
                continue
            sim = _cosine_similarity(embedding, doc["embedding"])
            scored.append({"agent_id": aid, "score": sim})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]
