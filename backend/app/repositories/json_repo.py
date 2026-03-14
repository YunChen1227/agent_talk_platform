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
from app.models.media import Media
from app.models.product import Product
from app.models.skill import Skill
from app.models.tag import TagCategory, Tag, AgentTag
from app.repositories.base import UserRepository, AgentRepository, MatcherRepository, SessionRepository, MessageRepository, MatchResultRepository, MediaRepository, ProductRepository, SkillRepository, TagCategoryRepository, TagRepository, AgentTagRepository

T = TypeVar("T", bound=BaseModel)

SYSTEM_MODELS = {"tagcategory", "tag"}


class JSONStore:
    def __init__(self, data_dir: str = None, seed_dir: str = None):
        from app.core.config import STORAGE_DIR
        if data_dir is None:
            data_dir = str(STORAGE_DIR / "dev")
        if seed_dir is None:
            seed_dir = str(STORAGE_DIR / "seed")
        self.data_dir = data_dir
        self.seed_dir = seed_dir
        for d in (data_dir, seed_dir):
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)

    def _base_dir_for(self, model_class: Type[T]) -> str:
        """System seed data lives in seed_dir; user data lives in data_dir."""
        if model_class.__name__.lower() in SYSTEM_MODELS:
            return self.seed_dir
        return self.data_dir

    def _get_path(self, model_class: Type[T]) -> str:
        base = self._base_dir_for(model_class)
        name = model_class.__name__.lower()
        if name == "media":
            return os.path.join(base, "media.json")
        if name == "product":
            return os.path.join(base, "products.json")
        if name == "skill":
            return os.path.join(base, "skills.json")
        if name == "tagcategory":
            return os.path.join(base, "tag_categories.json")
        if name == "tag":
            return os.path.join(base, "tags.json")
        if name == "agenttag":
            return os.path.join(base, "agent_tags.json")
        return os.path.join(base, f"{name}s.json")

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

    async def update(self, user: User) -> User:
        return self.store.add(user)

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

    async def list_all(self) -> List[Agent]:
        return self.store.list_all(Agent)

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

    async def find_all_by_agent(self, agent_id: UUID) -> List[Session]:
        sessions = self.store.list_all(Session)
        matched = [s for s in sessions if s.agent_a_id == agent_id or s.agent_b_id == agent_id]
        return sorted(matched, key=lambda x: x.created_at, reverse=True)

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

    async def update(self, result: MatchResult) -> MatchResult:
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
        from app.core.config import settings
        
        agents = self.store.load(Agent)
        sessions = self.store.load(Session)
        
        # 任何状态下只要聊过天，这一对 Agent 以后都不会再被匹配
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
                # 不和自己配对
                if candidate.id == agent.id:
                    continue
                # 同一个用户下的 Agent 不互相聊天
                if candidate.user_id == agent.user_id:
                    continue
                
                if (agent.id, candidate.id) in processed_pairs or (candidate.id, agent.id) in processed_pairs:
                    continue
                    
                # 之前任何状态下已经有过 Session 的双方，不再匹配
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


class JSONMediaRepository(MediaRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, media: Media) -> Media:
        if not media.id:
            media.id = uuid4()
        return self.store.add(media)

    async def get(self, media_id: UUID) -> Optional[Media]:
        return self.store.get(Media, media_id)

    async def list_by_user(self, user_id: UUID) -> List[Media]:
        all_media = self.store.list_all(Media)
        return [m for m in all_media if m.user_id == user_id]

    async def delete(self, media_id: UUID) -> bool:
        return self.store.delete(Media, media_id)


class JSONProductRepository(ProductRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, product: Product) -> Product:
        if not product.id:
            product.id = uuid4()
        return self.store.add(product)

    async def get(self, product_id: UUID) -> Optional[Product]:
        return self.store.get(Product, product_id)

    async def list_by_user(self, user_id: UUID) -> List[Product]:
        all_products = self.store.list_all(Product)
        return [p for p in all_products if p.user_id == user_id]

    async def update(self, product: Product) -> Product:
        return self.store.add(product)

    async def delete(self, product_id: UUID) -> bool:
        return self.store.delete(Product, product_id)


class JSONSkillRepository(SkillRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def create(self, skill: Skill) -> Skill:
        if not skill.id:
            skill.id = uuid4()
        return self.store.add(skill)

    async def get(self, skill_id: UUID) -> Optional[Skill]:
        return self.store.get(Skill, skill_id)

    async def list_by_user(self, user_id: UUID) -> List[Skill]:
        all_skills = self.store.list_all(Skill)
        return [s for s in all_skills if s.user_id == user_id]

    async def update(self, skill: Skill) -> Skill:
        return self.store.add(skill)

    async def delete(self, skill_id: UUID) -> bool:
        return self.store.delete(Skill, skill_id)


class JSONTagCategoryRepository(TagCategoryRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def list_active(self) -> List[TagCategory]:
        cats = self.store.list_all(TagCategory)
        return sorted(
            [c for c in cats if c.is_active],
            key=lambda c: c.sort_order,
        )

    async def get_by_slug(self, slug: str) -> Optional[TagCategory]:
        for c in self.store.list_all(TagCategory):
            if c.slug == slug:
                return c
        return None

    async def create(self, category: TagCategory) -> TagCategory:
        if not category.id:
            category.id = uuid4()
        return self.store.add(category)


class JSONTagRepository(TagRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def list_active(self) -> List[Tag]:
        tags = self.store.list_all(Tag)
        return sorted(
            [t for t in tags if t.is_active],
            key=lambda t: t.sort_order,
        )

    async def list_by_category(self, category_id: UUID) -> List[Tag]:
        tags = self.store.list_all(Tag)
        return sorted(
            [t for t in tags if t.category_id == category_id and t.is_active],
            key=lambda t: t.sort_order,
        )

    async def list_roots_by_category(self, category_id: UUID) -> List[Tag]:
        tags = self.store.list_all(Tag)
        return sorted(
            [t for t in tags if t.category_id == category_id and t.is_active and t.parent_id is None],
            key=lambda t: t.sort_order,
        )

    async def list_children(self, parent_id: UUID) -> List[Tag]:
        tags = self.store.list_all(Tag)
        return sorted(
            [t for t in tags if t.parent_id == parent_id and t.is_active],
            key=lambda t: t.sort_order,
        )

    async def get_by_slug(self, slug: str) -> Optional[Tag]:
        for t in self.store.list_all(Tag):
            if t.slug == slug:
                return t
        return None

    async def get_by_slugs(self, slugs: List[str]) -> List[Tag]:
        slug_set = set(slugs)
        return [t for t in self.store.list_all(Tag) if t.slug in slug_set]

    async def create(self, tag: Tag) -> Tag:
        if not tag.id:
            tag.id = uuid4()
        return self.store.add(tag)


class JSONAgentTagRepository(AgentTagRepository):
    def __init__(self, store: JSONStore):
        self.store = store

    async def set_tags(self, agent_id: UUID, tag_ids: List[UUID]) -> None:
        all_links = self.store.list_all(AgentTag)
        remaining = [link for link in all_links if link.agent_id != agent_id]
        for tid in tag_ids:
            remaining.append(AgentTag(agent_id=agent_id, tag_id=tid))
        self.store.save(AgentTag, remaining)

    async def get_tags_for_agent(self, agent_id: UUID) -> List[Tag]:
        links = self.store.list_all(AgentTag)
        tag_ids = {link.tag_id for link in links if link.agent_id == agent_id}
        all_tags = self.store.list_all(Tag)
        return [t for t in all_tags if t.id in tag_ids]

    async def get_agent_ids_by_tag_ids(self, tag_ids: List[UUID]) -> List[UUID]:
        tid_set = set(tag_ids)
        links = self.store.list_all(AgentTag)
        return list({link.agent_id for link in links if link.tag_id in tid_set})

    async def list_all(self) -> List[AgentTag]:
        return self.store.list_all(AgentTag)
