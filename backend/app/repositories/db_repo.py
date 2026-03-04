from typing import List, Optional, Tuple
from uuid import UUID
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.session import Session, SessionStatus, MatchResult
from app.models.message import Message
from app.repositories.base import UserRepository, AgentRepository, MatcherRepository, SessionRepository, MessageRepository, MatchResultRepository

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

    async def find_matches(self, threshold: float) -> List[Tuple[UUID, UUID]]:
        statement = select(Agent).where(Agent.status == AgentStatus.MATCHING)
        result = await self.session.exec(statement)
        agents = result.all()
        
        matched_pairs = []
        processed_pairs = set()
        
        for agent in agents:
            # Refresh to ensure status is current
            await self.session.refresh(agent)
            if agent.status != AgentStatus.MATCHING:
                continue
                
            user = await self.session.get(User, agent.user_id)
            if not user or user.embedding is None:
                continue
                
            # Find candidates
            stmt = select(Agent, User.embedding.cosine_distance(user.embedding)).join(User).where(
                Agent.status == AgentStatus.MATCHING,
                Agent.id != agent.id
            ).order_by(User.embedding.cosine_distance(user.embedding))
            
            candidate_results = (await self.session.exec(stmt)).all()
            
            for match in candidate_results:
                candidate, distance = match
                
                # Avoid duplicates in this batch
                if (candidate.id, agent.id) in processed_pairs or (agent.id, candidate.id) in processed_pairs:
                    continue

                if distance is not None and distance < threshold:
                    # Check for ANY existing session (active or completed) to prevent re-matching
                    existing_session_stmt = select(Session).where(
                        or_(
                            and_(Session.agent_a_id == agent.id, Session.agent_b_id == candidate.id),
                            and_(Session.agent_a_id == candidate.id, Session.agent_b_id == agent.id)
                        )
                    )
                    existing_session = (await self.session.exec(existing_session_stmt)).first()
                    
                    if existing_session:
                        continue

                    matched_pairs.append((agent.id, candidate.id))
                    processed_pairs.add((agent.id, candidate.id))
                    
                    # Do NOT update status to BUSY
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
