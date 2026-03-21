from typing import List, Optional, Tuple
from uuid import UUID
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.session import Session, SessionStatus, MatchResult
from app.models.message import Message
from app.models.media import Media
from app.models.product import Product
from app.models.skill import Skill
from app.models.tag import TagCategory, Tag, AgentTag
from app.repositories.base import (
    UserRepository, AgentRepository, MatcherRepository, SessionRepository,
    MessageRepository, MatchResultRepository, MediaRepository, ProductRepository,
    SkillRepository, TagCategoryRepository, TagRepository, AgentTagRepository,
)

class DBUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get(self, user_id: UUID) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        result = await self.session.exec(statement)
        return result.first()

    async def update(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

class DBAgentRepository(AgentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, agent: Agent) -> Agent:
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def get(self, agent_id: UUID) -> Optional[Agent]:
        return await self.session.get(Agent, agent_id)

    async def list_by_user(self, user_id: UUID) -> List[Agent]:
        statement = select(Agent).where(Agent.user_id == user_id)
        return (await self.session.exec(statement)).all()

    async def list_all(self) -> List[Agent]:
        statement = select(Agent)
        return (await self.session.exec(statement)).all()

    async def update_status(self, agent_id: UUID, status: AgentStatus) -> Optional[Agent]:
        agent = await self.get(agent_id)
        if agent:
            agent.status = status
            self.session.add(agent)
            await self.session.commit()
            await self.session.refresh(agent)
        return agent

    async def get_matching_candidates(self) -> List[Agent]:
        statement = select(Agent).where(Agent.status == AgentStatus.MATCHING)
        return (await self.session.exec(statement)).all()

    async def update(self, agent: Agent) -> Agent:
        self.session.add(agent)
        await self.session.commit()
        await self.session.refresh(agent)
        return agent

    async def delete(self, agent_id: UUID) -> bool:
        agent = await self.get(agent_id)
        if agent:
            await self.session.delete(agent)
            await self.session.commit()
            return True
        return False

class DBMatcherRepository(MatcherRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_matches(self, threshold: float, embedding_repo=None) -> List[Tuple[UUID, UUID]]:
        if embedding_repo is None:
            from app.core.deps import get_embedding_repo
            embedding_repo = get_embedding_repo()

        statement = select(Agent).where(Agent.status == AgentStatus.MATCHING)
        result = await self.session.exec(statement)
        agents = result.all()

        agent_map = {str(a.id): a for a in agents}
        matched_pairs = []
        processed_pairs = set()

        for agent in agents:
            agent_id_str = str(agent.id)

            if agent_id_str in {str(p) for pair in processed_pairs for p in pair}:
                continue

            embedding = await embedding_repo.get(agent_id_str)
            if embedding is None:
                continue

            exclude_ids = [agent_id_str]
            for a in agents:
                if a.user_id == agent.user_id and a.id != agent.id:
                    exclude_ids.append(str(a.id))

            hits = await embedding_repo.search_nearest(embedding, k=10, exclude_ids=exclude_ids)

            for hit in hits:
                score = hit["score"]
                distance = 1.0 - score
                if distance >= threshold:
                    continue

                candidate_id_str = hit["agent_id"]
                candidate = agent_map.get(candidate_id_str)
                if candidate is None:
                    continue

                pair_key = tuple(sorted([agent_id_str, candidate_id_str]))
                if pair_key in processed_pairs:
                    continue

                existing_session_stmt = select(Session).where(
                    or_(
                        and_(Session.agent_a_id == agent.id, Session.agent_b_id == candidate.id),
                        and_(Session.agent_a_id == candidate.id, Session.agent_b_id == agent.id),
                    )
                )
                existing_session = (await self.session.exec(existing_session_stmt)).first()
                if existing_session:
                    continue

                matched_pairs.append((agent.id, candidate.id))
                processed_pairs.add(pair_key)
                break

        return matched_pairs

class DBSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, session: Session) -> Session:
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def get(self, session_id: UUID) -> Optional[Session]:
        return await self.session.get(Session, session_id)

    async def list_active(self) -> List[Session]:
        statement = select(Session).where(Session.status == SessionStatus.ACTIVE)
        return (await self.session.exec(statement)).all()
        
    async def reset_judging_sessions(self) -> None:
        statement = select(Session).where(Session.status == SessionStatus.JUDGING)
        results = (await self.session.exec(statement)).all()
        for session in results:
            session.status = SessionStatus.ACTIVE
            self.session.add(session)
        if results:
            await self.session.commit()
        
    async def find_by_agent(self, agent_id: UUID) -> Optional[Session]:
        statement = select(Session).where(
            or_(Session.agent_a_id == agent_id, Session.agent_b_id == agent_id)
        ).order_by(Session.created_at.desc())
        result = (await self.session.exec(statement)).first()
        return result

    async def find_all_by_agent(self, agent_id: UUID) -> List[Session]:
        statement = select(Session).where(
            or_(Session.agent_a_id == agent_id, Session.agent_b_id == agent_id)
        ).order_by(Session.created_at.desc())
        return (await self.session.exec(statement)).all()

    async def update(self, session: Session) -> Session:
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

class DBMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_history(self, session_id: UUID) -> List[Message]:
        statement = select(Message).where(Message.session_id == session_id).order_by(Message.timestamp)
        return (await self.session.exec(statement)).all()

class DBMatchResultRepository(MatchResultRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, result: MatchResult) -> MatchResult:
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def update(self, result: MatchResult) -> MatchResult:
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_by_session_id(self, session_id: UUID) -> Optional[MatchResult]:
        statement = select(MatchResult).where(MatchResult.session_id == session_id)
        return (await self.session.exec(statement)).first()


class DBMediaRepository(MediaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, media: Media) -> Media:
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def get(self, media_id: UUID) -> Optional[Media]:
        return await self.session.get(Media, media_id)

    async def list_by_user(self, user_id: UUID) -> List[Media]:
        statement = select(Media).where(Media.user_id == user_id)
        return (await self.session.exec(statement)).all()

    async def delete(self, media_id: UUID) -> bool:
        media = await self.get(media_id)
        if media:
            await self.session.delete(media)
            await self.session.commit()
            return True
        return False


class DBProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get(self, product_id: UUID) -> Optional[Product]:
        return await self.session.get(Product, product_id)

    async def list_by_user(self, user_id: UUID) -> List[Product]:
        statement = select(Product).where(Product.user_id == user_id)
        return (await self.session.exec(statement)).all()

    async def update(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: UUID) -> bool:
        product = await self.get(product_id)
        if product:
            await self.session.delete(product)
            await self.session.commit()
            return True
        return False


class DBSkillRepository(SkillRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, skill: Skill) -> Skill:
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def get(self, skill_id: UUID) -> Optional[Skill]:
        return await self.session.get(Skill, skill_id)

    async def list_by_user(self, user_id: UUID) -> List[Skill]:
        statement = select(Skill).where(Skill.user_id == user_id)
        return (await self.session.exec(statement)).all()

    async def update(self, skill: Skill) -> Skill:
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def delete(self, skill_id: UUID) -> bool:
        skill = await self.get(skill_id)
        if skill:
            await self.session.delete(skill)
            await self.session.commit()
            return True
        return False


class DBTagCategoryRepository(TagCategoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> List[TagCategory]:
        statement = select(TagCategory).where(TagCategory.is_active == True).order_by(TagCategory.sort_order)
        return (await self.session.exec(statement)).all()

    async def list_active_by_scope(self, scope: str) -> List[TagCategory]:
        statement = (
            select(TagCategory)
            .where(TagCategory.is_active == True, TagCategory.scope == scope)
            .order_by(TagCategory.sort_order)
        )
        return (await self.session.exec(statement)).all()

    async def get_by_slug(self, slug: str) -> Optional[TagCategory]:
        statement = select(TagCategory).where(TagCategory.slug == slug)
        return (await self.session.exec(statement)).first()

    async def create(self, category: TagCategory) -> TagCategory:
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category


class DBTagRepository(TagRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> List[Tag]:
        statement = select(Tag).where(Tag.is_active == True).order_by(Tag.sort_order)
        return (await self.session.exec(statement)).all()

    async def list_active_by_scope(self, scope: str) -> List[Tag]:
        statement = (
            select(Tag)
            .join(TagCategory, Tag.category_id == TagCategory.id)
            .where(Tag.is_active == True, TagCategory.scope == scope)
            .order_by(Tag.sort_order)
        )
        return (await self.session.exec(statement)).all()

    async def list_by_category(self, category_id: UUID) -> List[Tag]:
        statement = select(Tag).where(
            Tag.category_id == category_id, Tag.is_active == True
        ).order_by(Tag.sort_order)
        return (await self.session.exec(statement)).all()

    async def list_roots_by_category(self, category_id: UUID) -> List[Tag]:
        statement = select(Tag).where(
            Tag.category_id == category_id,
            Tag.is_active == True,
            Tag.parent_id == None,
        ).order_by(Tag.sort_order)
        return (await self.session.exec(statement)).all()

    async def list_children(self, parent_id: UUID) -> List[Tag]:
        statement = select(Tag).where(
            Tag.parent_id == parent_id, Tag.is_active == True
        ).order_by(Tag.sort_order)
        return (await self.session.exec(statement)).all()

    async def get_by_slug(self, slug: str) -> Optional[Tag]:
        statement = select(Tag).where(Tag.slug == slug)
        return (await self.session.exec(statement)).first()

    async def get_by_slugs(self, slugs: List[str]) -> List[Tag]:
        statement = select(Tag).where(Tag.slug.in_(slugs))
        return (await self.session.exec(statement)).all()

    async def create(self, tag: Tag) -> Tag:
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def update(self, tag: Tag) -> Tag:
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def list_without_embedding(self) -> List[Tag]:
        rows = await self.list_active()
        return [t for t in rows if not t.embedding]


class DBAgentTagRepository(AgentTagRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_tags(self, agent_id: UUID, tag_ids: List[UUID]) -> None:
        statement = select(AgentTag).where(AgentTag.agent_id == agent_id)
        existing = (await self.session.exec(statement)).all()
        for link in existing:
            await self.session.delete(link)
        for tid in tag_ids:
            self.session.add(AgentTag(agent_id=agent_id, tag_id=tid))
        await self.session.commit()

    async def get_tags_for_agent(self, agent_id: UUID) -> List[Tag]:
        statement = (
            select(Tag)
            .join(AgentTag, AgentTag.tag_id == Tag.id)
            .where(AgentTag.agent_id == agent_id)
        )
        return (await self.session.exec(statement)).all()

    async def get_agent_ids_by_tag_ids(self, tag_ids: List[UUID]) -> List[UUID]:
        statement = select(AgentTag.agent_id).where(AgentTag.tag_id.in_(tag_ids)).distinct()
        return list((await self.session.exec(statement)).all())

    async def list_all(self) -> List[AgentTag]:
        statement = select(AgentTag)
        return (await self.session.exec(statement)).all()
