from uuid import UUID
from typing import Tuple, List, Union, Optional
from app.models.agent import Agent, AgentStatus
from app.models.user import User
from app.repositories.base import AgentRepository, UserRepository, TagRepository, AgentTagRepository, ProductRepository, EmbeddingRepository
from app.services.llm import get_random_client, extract_tags, get_embedding, extract_tags_from_catalog
import google.generativeai as genai

async def generate_system_prompt(user_demand: str, user_tags: List[str]) -> Tuple[str, str]:
    client_info = get_random_client()
    if not client_info:
        return f"System prompt for demand: {user_demand}", "Hello! I am looking for a match."

    prompt = f"""
    You are an AI agent representing a user with the following description: "{user_demand}".
    Key tags: {', '.join(user_tags)}.
    
    Your goal is to negotiate with other agents to find the best match for your user.
    
    Please generate two things:
    1. A comprehensive **System Prompt** for yourself to act as this agent.
    2. A short **Opening Remark** (1-2 sentences) to start a conversation with another agent.
    
    The system prompt should include:
    - **Role Definition**: Define your persona based on the demand.
    - **Core Objective**: Clearly state what you want to achieve.
    - **Negotiation Strategy**: How will you approach the negotiation?
    - **Constraints**: What are your deal-breakers?
    - **Tone and Style**: How should you speak?
    
    Output format:
    ---SYSTEM_PROMPT---
    (Your generated system prompt here)
    ---OPENING_REMARK---
    (Your generated opening remark here)
    """
    
    try:
        content = ""
        if client_info["provider"] == "gemini":
            model = genai.GenerativeModel(client_info["model"])
            response = await model.generate_content_async(prompt)
            content = response.text.strip()
        else:
            client = client_info["client"]
            response = await client.chat.completions.create(
                model="gpt-4" if client_info["provider"] == "openai" else client_info["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            
        parts = content.split("---OPENING_REMARK---")
        if len(parts) == 2:
            sys_prompt = parts[0].replace("---SYSTEM_PROMPT---", "").strip()
            opening = parts[1].strip()
            return sys_prompt, opening
        else:
            return content, "Hello! I am ready to negotiate."
            
    except Exception as e:
        print(f"Error generating system prompt: {e}")
        return f"System prompt for demand: {user_demand}", "Hello!"

async def create_agent(
    agent_repo: AgentRepository, 
    user_repo: UserRepository, 
    user_id: Union[str, UUID], 
    name: str,
    description: Optional[str] = None,
    system_prompt: Optional[str] = None,
    opening_remark: Optional[str] = None,
    linked_product_ids: Optional[List[UUID]] = None,
    linked_skill_ids: Optional[List[UUID]] = None,
    tag_repo: Optional[TagRepository] = None,
    agent_tag_repo: Optional[AgentTagRepository] = None,
    tag_ids: Optional[List[UUID]] = None,
    product_repo: Optional[ProductRepository] = None,
    embedding_repo: Optional[EmbeddingRepository] = None,
) -> Agent:
    if isinstance(user_id, str):
        user_id = UUID(user_id)
        
    user = await user_repo.get(user_id)
    if not user:
        raise ValueError("User not found")

    is_paid_flow = (description is not None) and (system_prompt is None)

    final_system_prompt = ""
    final_opening_remark = ""
    tags = []
    embedding = None

    if is_paid_flow:
        tags = await extract_tags(description)
        embedding = await get_embedding(description)
        final_system_prompt, final_opening_remark = await generate_system_prompt(description, tags)
    else:
        final_system_prompt = system_prompt or ""
        final_opening_remark = opening_remark or ""
        tags = await extract_tags(final_system_prompt)
        embedding = await get_embedding(final_system_prompt)
    
    agent = Agent(
        user_id=user_id,
        name=name,
        system_prompt=final_system_prompt,
        opening_remark=final_opening_remark,
        status=AgentStatus.IDLE,
        tags=tags,
        linked_product_ids=linked_product_ids or [],
        linked_skill_ids=linked_skill_ids or [],
    )
    created = await agent_repo.create(agent)

    if embedding and embedding_repo:
        await embedding_repo.upsert(str(created.id), embedding)

    if tag_repo and agent_tag_repo:
        if tag_ids:
            await _assign_manual_tags(created, tag_ids, tag_repo, agent_tag_repo)
        elif is_paid_flow:
            await _assign_catalog_tags(created, final_system_prompt, tag_repo, agent_tag_repo)

        if product_repo and linked_product_ids:
            await _inherit_product_tags(created, linked_product_ids, product_repo, agent_tag_repo)

    return created


async def _inherit_product_tags(
    agent: Agent,
    linked_product_ids: List[UUID],
    product_repo: ProductRepository,
    agent_tag_repo: AgentTagRepository,
) -> None:
    """Append tag_ids from all linked products to the agent's existing tags."""
    product_tag_ids: set = set()
    for pid in linked_product_ids:
        product = await product_repo.get(pid)
        if product and product.tag_ids:
            product_tag_ids.update(product.tag_ids)
    if not product_tag_ids:
        return
    existing_tags = await agent_tag_repo.get_tags_for_agent(agent.id)
    existing_ids = {t.id for t in existing_tags}
    merged = list(existing_ids | product_tag_ids)
    if len(merged) > len(existing_ids):
        await agent_tag_repo.set_tags(agent.id, merged)


async def _assign_manual_tags(
    agent: Agent,
    tag_ids: List[UUID],
    tag_repo: TagRepository,
    agent_tag_repo: AgentTagRepository,
) -> None:
    """Assign user-selected tags from the catalog."""
    all_tags = await tag_repo.list_active()
    valid_ids = {t.id for t in all_tags}
    filtered_ids = [tid for tid in tag_ids if tid in valid_ids]

    if filtered_ids:
        await agent_tag_repo.set_tags(agent.id, filtered_ids)

    tag_map = {t.id: t for t in all_tags}
    agent.tags = [tag_map[tid].name for tid in filtered_ids if tid in tag_map]


async def _assign_catalog_tags(
    agent: Agent,
    text: str,
    tag_repo: TagRepository,
    agent_tag_repo: AgentTagRepository,
) -> None:
    """Extract tags from predefined catalog via LLM and write to agent_tag relation."""
    all_tags = await tag_repo.list_active()
    if not all_tags:
        return

    catalog = {t.slug: t for t in all_tags}
    slugs = await extract_tags_from_catalog(text, list(catalog.keys()))

    matched_tag_ids = []
    matched_tag_names = []
    for slug in slugs:
        tag = catalog.get(slug)
        if tag:
            matched_tag_ids.append(tag.id)
            matched_tag_names.append(tag.name)

    if matched_tag_ids:
        await agent_tag_repo.set_tags(agent.id, matched_tag_ids)

    if matched_tag_names:
        agent.tags = matched_tag_names
