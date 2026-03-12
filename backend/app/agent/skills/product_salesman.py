"""
Built-in Skill: Product Salesman

Automatically activates when an Agent has linked products (linked_product_ids).
Injects product catalog context and strict selling constraints into the
system prompt, ensuring the Agent only promotes bound products.

Available to both FREE and PAID users.
"""

from typing import List, Optional, Tuple
from app.models.agent import Agent
from app.models.product import Product
from app.models.enums import ProductStatus
from app.repositories.base import ProductRepository


async def is_active(agent: Agent, product_repo: ProductRepository) -> bool:
    """Check whether the Product Salesman skill should activate for this agent."""
    if not agent.linked_product_ids:
        return False

    for pid in agent.linked_product_ids:
        product = await product_repo.get(pid)
        if product and product.status == ProductStatus.ACTIVE:
            return True
    return False


async def build_product_catalog(
    agent: Agent, product_repo: ProductRepository
) -> List[Product]:
    """Load all ACTIVE products linked to the agent."""
    if not agent.linked_product_ids:
        return []

    products: List[Product] = []
    for pid in agent.linked_product_ids:
        product = await product_repo.get(pid)
        if product and product.status == ProductStatus.ACTIVE:
            products.append(product)
    return products


def _format_catalog(products: List[Product]) -> str:
    """Format products into a structured catalog string for prompt injection."""
    lines: List[str] = []
    for idx, p in enumerate(products, 1):
        lines.append(f"商品 {idx}:")
        lines.append(f"  - 名称: {p.name}")
        lines.append(f"  - 价格: {p.price} {p.currency}")
        if p.description:
            lines.append(f"  - 描述: {p.description}")
        lines.append(f"  - 商品ID: {p.id}")
        lines.append("")
    return "\n".join(lines)


def build_salesman_prompt(products: List[Product]) -> str:
    """Build the constraint prompt fragment to append after the agent's system_prompt."""
    catalog_text = _format_catalog(products)
    product_names = "、".join(p.name for p in products)

    return (
        "\n\n=== 商品推销规则 (强制) ===\n"
        "你是一名专业销售代表。在本次对话中，你必须严格遵守以下规则:\n\n"
        f"1. **只推销目录中的商品**: 你只能推荐、介绍和推销下方「商品目录」中列出的商品 ({product_names})。\n"
        "2. **允许对比竞品**: 你可以提及市面上的竞品信息做对比分析，但仅用于突出目录中商品的优势。所有对比的最终结论必须引导到目录中的商品。\n"
        "3. **禁止推荐外部商品**: 严禁建议对方购买任何不在目录中的商品，严禁提供外部购买链接或推荐替代品。\n"
        "4. **自然推销**: 在对话中自然地介绍商品，根据对方需求匹配目录中最合适的商品，不要生硬推销。\n"
        "5. **诚实描述**: 基于商品目录中的信息如实描述商品，不虚构不存在的功能或特性。\n\n"
        "【商品目录】\n"
        f"{catalog_text}"
        "=== 规则结束 ===\n"
    )


def validate_response(response: str, products: List[Product]) -> Tuple[bool, Optional[str]]:
    """
    Lightweight post-generation check.

    Returns (is_valid, reason). Checks that the response does not explicitly
    recommend purchasing a product whose name is clearly not in the catalog.
    This is a best-effort heuristic, not a hard guarantee.
    """
    if not products or not response:
        return True, None

    product_names_lower = {p.name.lower() for p in products}

    recommendation_phrases = [
        "推荐你购买", "建议你买", "你可以买", "不如试试",
        "推荐购买", "建议购买", "recommend", "suggest buying",
        "you should buy", "check out",
    ]

    for phrase in recommendation_phrases:
        phrase_lower = phrase.lower()
        idx = response.lower().find(phrase_lower)
        if idx == -1:
            continue
        after_phrase = response[idx + len(phrase):idx + len(phrase) + 60].strip()
        if not after_phrase:
            continue
        found_in_catalog = any(name in after_phrase.lower() for name in product_names_lower)
        if not found_in_catalog:
            return False, f"回复中可能推荐了非绑定商品 (在 '{phrase}' 之后)"

    return True, None


RETRY_REINFORCEMENT = (
    "\n\n【重要提醒】你上一次回复违反了商品推销规则，推荐了不在商品目录中的产品。"
    "请重新生成回复，严格只推荐商品目录中的商品。不要推荐任何外部产品。"
)
