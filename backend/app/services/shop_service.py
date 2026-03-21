from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.models.product import Product
from app.models.enums import ProductStatus
from app.repositories.base import ProductRepository, AgentRepository, TagRepository


async def _assert_product_scope_tags(
    tag_repo: TagRepository,
    tag_ids: List[UUID],
) -> None:
    """Products may only use tags under product-scope categories."""
    if not tag_ids:
        return
    product_tags = await tag_repo.list_active_by_scope("product")
    valid_ids = {t.id for t in product_tags}
    for tid in tag_ids:
        if tid not in valid_ids:
            raise ValueError(
                f"Tag {tid} is not a product-scope tag. "
                "Products can only use product-scope tags."
            )


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
    tag_repo: Optional[TagRepository] = None,
) -> Product:
    image_ids = image_ids or []
    linked_agent_ids = linked_agent_ids or []
    tag_ids = tag_ids or []
    if tag_repo is not None:
        await _assert_product_scope_tags(tag_repo, tag_ids)
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
    return product


async def update_product(
    product_repo: ProductRepository,
    agent_repo: AgentRepository,
    product_id: UUID,
    user_id: UUID,
    tag_repo: Optional[TagRepository] = None,
    **kwargs,
) -> Optional[Product]:
    product = await product_repo.get(product_id)
    if not product or product.user_id != user_id:
        return None
    if tag_repo is not None and "tag_ids" in kwargs and kwargs["tag_ids"] is not None:
        await _assert_product_scope_tags(tag_repo, kwargs["tag_ids"])
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
        product.linked_agent_ids = list(new_ids)
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
