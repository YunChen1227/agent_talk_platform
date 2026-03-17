from typing import List, Optional, Dict
from elasticsearch import AsyncElasticsearch
from app.core.config import settings

AGENT_EMBEDDING_INDEX = "agent_embeddings"
EMBEDDING_DIM = 1536

es_client: Optional[AsyncElasticsearch] = None


def get_es_client() -> AsyncElasticsearch:
    global es_client
    if es_client is None:
        es_client = AsyncElasticsearch(hosts=[settings.ES_URL])
    return es_client


async def init_es():
    """Create the agent_embeddings index with dense_vector mapping if it does not exist."""
    client = get_es_client()
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


async def upsert_embedding(agent_id: str, embedding: List[float]):
    """Index or update an agent's embedding vector (doc id = agent_id)."""
    client = get_es_client()
    await client.index(
        index=AGENT_EMBEDDING_INDEX,
        id=agent_id,
        document={"agent_id": agent_id, "embedding": embedding},
        refresh="wait_for",
    )


async def delete_embedding(agent_id: str):
    """Remove an agent's embedding from the index."""
    client = get_es_client()
    try:
        await client.delete(index=AGENT_EMBEDDING_INDEX, id=agent_id, refresh="wait_for")
    except Exception:
        pass


async def search_nearest(
    embedding: List[float],
    k: int = 10,
    exclude_ids: Optional[List[str]] = None,
) -> List[Dict]:
    """
    kNN search for the nearest agent embeddings.
    Returns list of {"agent_id": str, "score": float} sorted by descending similarity.
    """
    client = get_es_client()

    knn_query: Dict = {
        "field": "embedding",
        "query_vector": embedding,
        "k": k,
        "num_candidates": max(k * 4, 50),
    }
    if exclude_ids:
        knn_query["filter"] = {"bool": {"must_not": [{"ids": {"values": exclude_ids}}]}}

    resp = await client.search(
        index=AGENT_EMBEDDING_INDEX,
        knn=knn_query,
        size=k,
    )

    results = []
    for hit in resp["hits"]["hits"]:
        results.append({
            "agent_id": hit["_source"]["agent_id"],
            "score": hit["_score"],
        })
    return results


async def close_es():
    global es_client
    if es_client is not None:
        await es_client.close()
        es_client = None
