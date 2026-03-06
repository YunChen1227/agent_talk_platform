import json
import os
import math
from typing import List, Optional, Tuple, Dict, Any, Type, TypeVar
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel

from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.session import Session, SessionStatus, MatchResult
from app.models.message import Message
from app.repositories.base import UserRepository, AgentRepository, MatcherRepository, SessionRepository, MessageRepository, MatchResultRepository

T = TypeVar("T", bound=BaseModel)

class JSONStore:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _get_path(self, model_class: Type[T]) -> str:
        return os.path.join(self.data_dir, f"{model_class.__name__.lower()}s.json")

    def load(self, model_class: Type[T]) -> List[T]:
        path = self._get_path(model_class)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return [model_class.model_validate(item) for item in data]
            except json.JSONDecodeError:
                return []

    def save(self, model_class: Type[T], items: List[T]):
        path = self._get_path(model_class)
        # Convert to dict, handling UUID and datetime
        data = [json.loads(item.model_dump_json()) for item in items]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add(self, item: T):
        items = self.load(type(item))
        # Check if exists (update) or new
        # Assuming ID exists
        for i, existing in enumerate(items):
            if existing.id == item.id:
                items[i] = item
                self.save(type(item), items)
                return item
        items.append(item)
        self.save(type(item), items)
        return item

    def get(self, model_class: Type[T], id: UUID) -> Optional[T]:
        items = self.load(model_class)
        for item in items:
            if item.id == id:
                return item
        return None

    def delete(self, model_class: Type[T], id: UUID) -> bool:
        items = self.load(model_class)
        initial_len = len(items)
        items = [item for item in items if item.id != id]
        if len(items) < initial_len:
            self.save(model_class, items)
            return True
        return False

    def list_all(self, model_class: Type[T]) -> List[T]:
        return self.load(model_class)

class JSONUserRepository(UserRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, user: User) -> User:
        if not user.id:
            user.id = uuid4()
        return self.store.add(user)

    async def get(self, user_id: UUID) -> Optional[User]:
        return self.store.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        users = self.store.list_all(User)
        for user in users:
            if user.username == username:
                return user
        return None

class JSONAgentRepository(AgentRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, agent: Agent) -> Agent:
        if not agent.id:
            agent.id = uuid4()
        return self.store.add(agent)

    async def get(self, agent_id: UUID) -> Optional[Agent]:
        return self.store.get(Agent, agent_id)

    async def list_by_user(self, user_id: UUID) -> List[Agent]:
        agents = self.store.list_all(Agent)
        return [a for a in agents if a.user_id == user_id]

    async def update_status(self, agent_id: UUID, status: AgentStatus) -> Optional[Agent]:
        agent = await self.get(agent_id)
        if agent:
            agent.status = status
            self.store.add(agent)
        return agent
        
    async def get_matching_candidates(self) -> List[Agent]:
        agents = await self.list_all()
        return [a for a in agents if a.status == AgentStatus.MATCHING]

    async def update(self, agent: Agent) -> Agent:
        return self.store.add(agent)

    async def delete(self, agent_id: UUID) -> bool:
        return self.store.delete(Agent, agent_id)

class JSONSessionRepository(SessionRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, session: Session) -> Session:
        if not session.id:
            session.id = uuid4()
        return self.store.add(session)

    async def get(self, session_id: UUID) -> Optional[Session]:
        return self.store.get(Session, session_id)
        
    async def list_active(self) -> List[Session]:
        sessions = self.store.list_all(Session)
        return [s for s in sessions if s.status == SessionStatus.ACTIVE]
        
    async def reset_judging_sessions(self) -> None:
        sessions = self.store.list_all(Session)
        updated = False
        for s in sessions:
            if s.status == SessionStatus.JUDGING:
                s.status = SessionStatus.ACTIVE
                updated = True
        if updated:
            self.store.save(Session, sessions)
        
    async def find_by_agent(self, agent_id: UUID) -> Optional[Session]:
        sessions = self.store.list_all(Session)
        for s in sorted(sessions, key=lambda x: x.created_at, reverse=True):
            if s.agent_a_id == agent_id or s.agent_b_id == agent_id:
                return s
        return None

    async def update(self, session: Session) -> Session:
        return self.store.add(session)

class JSONMessageRepository(MessageRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, message: Message) -> Message:
        if not message.id:
            message.id = uuid4()
        return self.store.add(message)

    async def get_history(self, session_id: UUID) -> List[Message]:
        messages = self.store.list_all(Message)
        return sorted(
            [m for m in messages if m.session_id == session_id],
            key=lambda x: x.timestamp
        )

class JSONMatchResultRepository(MatchResultRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, result: MatchResult) -> MatchResult:
        if not result.id:
            result.id = uuid4()
        return self.store.add(result)

    async def get_by_session_id(self, session_id: UUID) -> Optional[MatchResult]:
        results = self.store.list_all(MatchResult)
        for r in results:
            if r.session_id == session_id:
                return r
        return None

class JSONMatcherRepository(MatcherRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    async def find_matches(self, threshold: float) -> List[Tuple[UUID, UUID]]:
        agents = self.store.load(Agent)
        sessions = self.store.load(Session)
        
        existing_pairs = set()
        for s in sessions:
            existing_pairs.add((s.agent_a_id, s.agent_b_id))
            existing_pairs.add((s.agent_b_id, s.agent_a_id))
        
        matching_agents = [a for a in agents if a.status == AgentStatus.MATCHING]
        matched_pairs = []
        processed_pairs = set()

        for agent in matching_agents:
            if not agent.embedding:
                continue

            best_match = None
            min_dist = float('inf')

            for candidate in matching_agents:
                if candidate.id == agent.id:
                    continue
                
                if (agent.id, candidate.id) in processed_pairs or (candidate.id, agent.id) in processed_pairs:
                    continue
                    
                if (agent.id, candidate.id) in existing_pairs:
                    continue
                
                if not candidate.embedding:
                    continue

                similarity = self._cosine_similarity(agent.embedding, candidate.embedding)
                distance = 1 - similarity

                if distance < min_dist:
                    min_dist = distance
                    best_match = candidate

            if best_match and min_dist < threshold:
                matched_pairs.append((agent.id, best_match.id))
                processed_pairs.add((agent.id, best_match.id))
                
        return matched_pairs
