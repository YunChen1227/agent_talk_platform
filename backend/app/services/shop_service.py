from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.models.product import Product
from app.models.enums import ProductStatus
from app.repositories.base import ProductRepository, AgentRepository, AgentTagRepository


async def _sync_product_tags_to_agent(
    agent_id: UUID,
    product_tag_ids: List[UUID],
    agent_tag_repo: AgentTagRepository,
) -> None:
    """Append product tag_ids to agent's existing tags (union, no overwrite)."""
    if not product_tag_ids:
        return
    existing_tags = await agent_tag_repo.get_tags_for_agent(agent_id)
    existing_ids = {t.id for t in existing_tags}
    merged = list(existing_ids | set(product_tag_ids))
    if len(merged) > len(existing_ids):
        await agent_tag_repo.set_tags(agent_id, merged)


async def create_product(
    product_repo: ProductRepository,
    agent_repo: AgentRepository,
    user_id: UUID,
    name: str,
    price: Decimal,
    description: Optional[str] = None,
    currency: str = "CNY",
    image_ids: Optional[List[UUID]] = None,
    cover_image_id: Optional[UUID] = None,
    linked_agent_ids: Optional[List[UUID]] = None,
    tag_ids: Optional[List[UUID]] = None,
    agent_tag_repo: Optional[AgentTagRepository] = None,
) -> Product:
    image_ids = image_ids or []
    linked_agent_ids = linked_agent_ids or []
    tag_ids = tag_ids or []
    product = Product(
        user_id=user_id,
        name=name,
        description=description or "",
        price=price,
        currency=currency,
        images=image_ids,
        cover_image_id=cover_image_id,
        status=ProductStatus.ACTIVE,
        linked_agent_ids=linked_agent_ids,
        tag_ids=tag_ids,
    )
    product = await product_repo.create(product)
    for agent_id in linked_agent_ids:
        agent = await agent_repo.get(agent_id)
        if agent and agent.user_id == user_id:
            ids = list(agent.linked_product_ids or [])
            if product.id not in ids:
                ids.append(product.id)
                agent.linked_product_ids = ids
                await agent_repo.update(agent)
            if agent_tag_repo and tag_ids:
                await _sync_product_tags_to_agent(agent_id, tag_ids, agent_tag_repo)
    return product


async def update_product(
    product_repo: ProductRepository,
    agent_repo: AgentRepository,
    product_id: UUID,
    user_id: UUID,
    agent_tag_repo: Optional[AgentTagRepository] = None,
    **kwargs,
) -> Optional[Product]:
    product = await product_repo.get(product_id)
    if not product or product.user_id != user_id:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(product, key):
            setattr(product, key, value)
    product.updated_at = datetime.utcnow()
    if "linked_agent_ids" in kwargs:
        old_ids = set(product.linked_agent_ids or [])
        new_ids = set(kwargs["linked_agent_ids"] or [])
        for agent_id in old_ids - new_ids:
            agent = await agent_repo.get(agent_id)
            if agent and agent.linked_product_ids:
                agent.linked_product_ids = [p for p in agent.linked_product_ids if p != product_id]
                await agent_repo.update(agent)
        for agent_id in new_ids - old_ids:
            agent = await agent_repo.get(agent_id)
            if agent and agent.user_id == user_id:
                ids = list(agent.linked_product_ids or [])
                if product_id not in ids:
                    ids.append(product_id)
                    agent.linked_product_ids = ids
                    await agent_repo.update(agent)
                if agent_tag_repo and product.tag_ids:
                    await _sync_product_tags_to_agent(agent_id, product.tag_ids, agent_tag_repo)
        product.linked_agent_ids = list(new_ids)
    elif agent_tag_repo and "tag_ids" in kwargs and kwargs["tag_ids"] is not None:
        for agent_id in (product.linked_agent_ids or []):
            await _sync_product_tags_to_agent(agent_id, kwargs["tag_ids"], agent_tag_repo)
    return await product_repo.update(product)


async def delete_product(
    product_repo: ProductRepository,
    agent_repo: AgentRepository,
    product_id: UUID,
    user_id: UUID,
) -> bool:
    product = await product_repo.get(product_id)
    if not product or product.user_id != user_id:
        return False
    for agent_id in product.linked_agent_ids or []:
        agent = await agent_repo.get(agent_id)
        if agent and agent.linked_product_ids:
            agent.linked_product_ids = [p for p in agent.linked_product_ids if p != product_id]
            await agent_repo.update(agent)
    return await product_repo.delete(product_id)


async def link_agent_to_product(
    product_repo: ProductRepository,
    agent_repo: AgentRepository,
    product_id: UUID,
    agent_id: UUID,
    user_id: UUID,
    agent_tag_repo: Optional[AgentTagRepository] = None,
) -> bool:
    product = await product_repo.get(product_id)
    agent = await agent_repo.get(agent_id)
    if not product or product.user_id != user_id:
        return False
    if not agent or agent.user_id != user_id:
        return False
    ids = list(product.linked_agent_ids or [])
    if agent_id not in ids:
        ids.append(agent_id)
        product.linked_agent_ids = ids
        await product_repo.update(product)
    agent_ids = list(agent.linked_product_ids or [])
    if product_id not in agent_ids:
        agent_ids.append(product_id)
        agent.linked_product_ids = agent_ids
        await agent_repo.update(agent)
    if agent_tag_repo and product.tag_ids:
        await _sync_product_tags_to_agent(agent_id, product.tag_ids, agent_tag_repo)
    return True


async def unlink_agent_from_product(
    product_repo: ProductRepository,
    agent_repo: AgentRepository,
    product_id: UUID,
    agent_id: UUID,
    user_id: UUID,
) -> bool:
    product = await product_repo.get(product_id)
    agent = await agent_repo.get(agent_id)
    if not product or product.user_id != user_id:
        return False
    if not agent:
        return False
    if product.linked_agent_ids and agent_id in product.linked_agent_ids:
        product.linked_agent_ids = [a for a in product.linked_agent_ids if a != agent_id]
        await product_repo.update(product)
    if agent.linked_product_ids and product_id in agent.linked_product_ids:
        agent.linked_product_ids = [p for p in agent.linked_product_ids if p != product_id]
        await agent_repo.update(agent)
    return True
