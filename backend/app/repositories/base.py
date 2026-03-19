from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.session import Session, MatchResult
from app.models.message import Message
from app.models.media import Media
from app.models.product import Product
from app.models.skill import Skill
from app.models.tag import TagCategory, Tag, AgentTag


class EmbeddingRepository(ABC):
    """Abstract interface for vector embedding storage (ES / JSON / etc.)."""

    @abstractmethod
    async def init(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def upsert(self, agent_id: str, embedding: List[float]) -> None:
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        pass

    @abstractmethod
    async def get(self, agent_id: str) -> Optional[List[float]]:
        pass

    @abstractmethod
    async def search_nearest(
        self,
        embedding: List[float],
        k: int = 10,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Return list of {\"agent_id\": str, \"score\": float}."""
        pass

class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

class AgentRepository(ABC):
    @abstractmethod
    async def create(self, agent: Agent) -> Agent:
        pass

    @abstractmethod
    async def get(self, agent_id: UUID) -> Optional[Agent]:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Agent]:
        pass

    @abstractmethod
    async def list_all(self) -> List[Agent]:
        pass

    @abstractmethod
    async def update_status(self, agent_id: UUID, status: AgentStatus) -> Optional[Agent]:
        pass
        
    @abstractmethod
    async def get_matching_candidates(self) -> List[Agent]:
        pass

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        pass

    @abstractmethod
    async def delete(self, agent_id: UUID) -> bool:
        pass

class MatcherRepository(ABC):
    @abstractmethod
    async def find_matches(self, threshold: float, embedding_repo: "EmbeddingRepository") -> List[Tuple[UUID, UUID]]:
        pass

class SessionRepository(ABC):
    @abstractmethod
    async def create(self, session: Session) -> Session:
        pass

    @abstractmethod
    async def get(self, session_id: UUID) -> Optional[Session]:
        pass
        
    @abstractmethod
    async def list_active(self) -> List[Session]:
        pass
        
    @abstractmethod
    async def reset_judging_sessions(self) -> None:
        pass

    @abstractmethod
    async def find_by_agent(self, agent_id: UUID) -> Optional[Session]:
        pass

    @abstractmethod
    async def find_all_by_agent(self, agent_id: UUID) -> List[Session]:
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        pass

class MessageRepository(ABC):
    @abstractmethod
    async def create(self, message: Message) -> Message:
        pass

    @abstractmethod
    async def get_history(self, session_id: UUID) -> List[Message]:
        pass

class MatchResultRepository(ABC):
    @abstractmethod
    async def create(self, result: MatchResult) -> MatchResult:
        pass

    @abstractmethod
    async def update(self, result: MatchResult) -> MatchResult:
        pass

    @abstractmethod
    async def get_by_session_id(self, session_id: UUID) -> Optional[MatchResult]:
        pass


class MediaRepository(ABC):
    @abstractmethod
    async def create(self, media: Media) -> Media:
        pass

    @abstractmethod
    async def get(self, media_id: UUID) -> Optional[Media]:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Media]:
        pass

    @abstractmethod
    async def delete(self, media_id: UUID) -> bool:
        pass


class ProductRepository(ABC):
    @abstractmethod
    async def create(self, product: Product) -> Product:
        pass

    @abstractmethod
    async def get(self, product_id: UUID) -> Optional[Product]:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Product]:
        pass

    @abstractmethod
    async def update(self, product: Product) -> Product:
        pass

    @abstractmethod
    async def delete(self, product_id: UUID) -> bool:
        pass


class SkillRepository(ABC):
    @abstractmethod
    async def create(self, skill: Skill) -> Skill:
        pass

    @abstractmethod
    async def get(self, skill_id: UUID) -> Optional[Skill]:
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Skill]:
        pass

    @abstractmethod
    async def update(self, skill: Skill) -> Skill:
        pass

    @abstractmethod
    async def delete(self, skill_id: UUID) -> bool:
        pass


class TagCategoryRepository(ABC):
    @abstractmethod
    async def list_active(self) -> List[TagCategory]:
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[TagCategory]:
        pass

    @abstractmethod
    async def create(self, category: TagCategory) -> TagCategory:
        pass


class TagRepository(ABC):
    @abstractmethod
    async def list_active(self) -> List[Tag]:
        pass

    @abstractmethod
    async def list_by_category(self, category_id: UUID) -> List[Tag]:
        pass

    @abstractmethod
    async def list_roots_by_category(self, category_id: UUID) -> List[Tag]:
        """Return only top-level tags (parent_id is None) in a category."""
        pass

    @abstractmethod
    async def list_children(self, parent_id: UUID) -> List[Tag]:
        """Return direct children of a tag."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Tag]:
        pass

    @abstractmethod
    async def get_by_slugs(self, slugs: List[str]) -> List[Tag]:
        pass

    @abstractmethod
    async def create(self, tag: Tag) -> Tag:
        pass


class AgentTagRepository(ABC):
    @abstractmethod
    async def set_tags(self, agent_id: UUID, tag_ids: List[UUID]) -> None:
        """Replace all tags for an agent."""
        pass

    @abstractmethod
    async def get_tags_for_agent(self, agent_id: UUID) -> List[Tag]:
        pass

    @abstractmethod
    async def get_agent_ids_by_tag_ids(self, tag_ids: List[UUID]) -> List[UUID]:
        """Return agent IDs that have at least one of the given tags."""
        pass

    @abstractmethod
    async def list_all(self) -> List[AgentTag]:
        pass