from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Body

from app.schemas.product import ProductCreate, ProductUpdate, ProductRead, LinkAgentBody, LinkAgentBody
from app.repositories.base import ProductRepository, AgentRepository
from app.core.deps import get_product_repo, get_agent_repo
from app.services.shop_service import (
    create_product as svc_create_product,
    update_product as svc_update_product,
    delete_product as svc_delete_product,
    link_agent_to_product as svc_link_agent,
    unlink_agent_from_product as svc_unlink_agent,
)
router = APIRouter()


def _to_read(p) -> ProductRead:
    return ProductRead(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        description=p.description,
        price=p.price,
        currency=p.currency,
        images=p.images or [],
        cover_image_id=p.cover_image_id,
        status=p.status,
        linked_agent_ids=p.linked_agent_ids or [],
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.post("/products", response_model=ProductRead)
async def api_create_product(
    body: ProductCreate,
    product_repo: ProductRepository = Depends(get_product_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    product = await svc_create_product(
        product_repo,
        agent_repo,
        body.user_id,
        body.name,
        body.price,
        description=body.description,
        currency=body.currency,
        image_ids=body.image_ids,
        cover_image_id=body.cover_image_id,
        linked_agent_ids=body.linked_agent_ids,
    )
    return _to_read(product)


@router.get("/products", response_model=List[ProductRead])
async def api_list_products(
    user_id: UUID,
    product_repo: ProductRepository = Depends(get_product_repo),
):
    items = await product_repo.list_by_user(user_id)
    return [_to_read(p) for p in items]


@router.get("/products/{product_id}", response_model=ProductRead)
async def api_get_product(
    product_id: UUID,
    user_id: UUID,
    product_repo: ProductRepository = Depends(get_product_repo),
):
    product = await product_repo.get(product_id)
    if not product or product.user_id != user_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_read(product)


@router.put("/products/{product_id}", response_model=ProductRead)
async def api_update_product(
    product_id: UUID,
    user_id: UUID,
    body: ProductUpdate,
    product_repo: ProductRepository = Depends(get_product_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    kwargs = body.model_dump(exclude_unset=True)
    if "image_ids" in kwargs:
        kwargs["images"] = kwargs.pop("image_ids")
    product = await svc_update_product(product_repo, agent_repo, product_id, user_id, **kwargs)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_read(product)


@router.delete("/products/{product_id}", status_code=204)
async def api_delete_product(
    product_id: UUID,
    user_id: UUID,
    product_repo: ProductRepository = Depends(get_product_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    ok = await svc_delete_product(product_repo, agent_repo, product_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return


@router.post("/products/{product_id}/link-agent")
async def api_link_agent(
    product_id: UUID,
    body: LinkAgentBody,
    product_repo: ProductRepository = Depends(get_product_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    ok = await svc_link_agent(product_repo, agent_repo, product_id, body.agent_id, body.user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Product or agent not found or not owned by user")
    return {"ok": True}


@router.post("/products/{product_id}/unlink-agent")
async def api_unlink_agent(
    product_id: UUID,
    body: LinkAgentBody,
    product_repo: ProductRepository = Depends(get_product_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
):
    ok = await svc_unlink_agent(product_repo, agent_repo, product_id, body.agent_id, body.user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Product or agent not found or not owned by user")
    return {"ok": True}
