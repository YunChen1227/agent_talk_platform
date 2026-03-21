from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List


class TagCreate(BaseModel):
    name: str
    category_id: UUID


class TagEmbedRequest(BaseModel):
    """Batch (re)compute tag embeddings via local embedding service."""

    force_all: bool = False


class TagEmbedResponse(BaseModel):
    updated: int


class TagRead(BaseModel):
    id: str
    name: str
    slug: str
    children: List["TagRead"] = []


class TagCategoryRead(BaseModel):
    id: str
    name: str
    slug: str
    tags: List[TagRead]


class AgentTagRead(BaseModel):
    id: str
    name: str
    slug: str
    category_id: str
    parent_id: Optional[str] = None


class MatchDetailRead(BaseModel):
    my_agent_id: str
    my_agent_name: str
    session_id: str
    status: str
    created_at: str


class PlazaAgentRead(BaseModel):
    id: str
    name: str
    tags: List[AgentTagRead]
    opening_remark: Optional[str] = None
    match_status: str
    match_details: List[MatchDetailRead]
    search_score: Optional[float] = None


class PlazaSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PlazaAgentRead]
