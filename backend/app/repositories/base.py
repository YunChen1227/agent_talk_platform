from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any
from uuid import UUID
from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.session import Session, MatchResult
from app.models.message import Message
from app.models.media import Media
from app.models.product import Product

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
    async def find_matches(self, threshold: float) -> List[Tuple[UUID, UUID]]:
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