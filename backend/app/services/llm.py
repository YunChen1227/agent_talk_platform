from typing import List, Dict, Any, Optional
import json
import random
import httpx
from openai import AsyncOpenAI
from app.core.config import settings

# Global dictionary to store valid clients
valid_clients = {}

def validate_api_keys():
    """
    Validates API keys from settings and populates valid_clients.
    """
    global valid_clients
    valid_clients = {}
    print("Starting API key validation...")

    # DeepSeek
    if settings.DEEPSEEK_API_KEY:
        try:
            client = AsyncOpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
            valid_clients["deepseek"] = {"client": client, "model": "deepseek-chat"}
            print("DeepSeek API key configured.")
        except Exception as e:
            print(f"DeepSeek validation failed: {e}")

    # Qwen
    if settings.QWEN_API_KEY:
        try:
            client = AsyncOpenAI(api_key=settings.QWEN_API_KEY, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
            valid_clients["qwen"] = {"client": client, "model": "qwen-turbo"}
            print("Qwen API key configured.")
        except Exception as e:
            print(f"Qwen validation failed: {e}")

    # OpenAI
    if settings.OPENAI_API_KEY:
        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            valid_clients["openai"] = {"client": client, "model": "gpt-3.5-turbo"}
            print("OpenAI API key configured.")
        except Exception as e:
            print(f"OpenAI validation failed: {e}")

    # UCloud
    if settings.UCLOUD_API_KEY:
        try:
            client = AsyncOpenAI(api_key=settings.UCLOUD_API_KEY, base_url="https://api.modelverse.cn/v1/")
            valid_clients["ucloud"] = {"client": client, "model": "qwen3.5-plus"}
            print("UCloud API key configured.")
        except Exception as e:
            print(f"UCloud validation failed: {e}")

    print(f"Validation complete. Valid providers: {list(valid_clients.keys())}")


def get_random_client() -> Optional[Dict[str, Any]]:
    if not valid_clients:
        return None
    provider = random.choice(list(valid_clients.keys()))
    return {"provider": provider, **valid_clients[provider]}


def _mock_embedding() -> List[float]:
    return [random.random() for _ in range(max(1, int(settings.EMBEDDING_DIM)))]


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Batch embeddings via local OpenAI-compatible service (EMBEDDING_API_URL).
    Returns one vector per input string, same order.
    """
    if not texts:
        return []
    url = (settings.EMBEDDING_API_URL or "").strip()
    if not url:
        return [_mock_embedding() for _ in texts]

    payload: Dict[str, Any] = {
        "input": texts if len(texts) > 1 else texts[0],
        "model": "qwen3-embedding",
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            body = resp.json()
        data = body.get("data") or []
        by_index = sorted(data, key=lambda x: x.get("index", 0))
        out = [item["embedding"] for item in by_index]
        if len(out) != len(texts):
            raise ValueError(
                f"Embedding API returned {len(out)} vectors for {len(texts)} inputs"
            )
        return out
    except Exception as e:
        print(f"[embedding] Error calling {url}: {e}")
        return [_mock_embedding() for _ in texts]


async def get_embedding(text: str) -> List[float]:
    vecs = await get_embeddings([text])
    return vecs[0] if vecs else _mock_embedding()


async def extract_tags(text: str) -> List[str]:
    if settings.is_dev:
        print("[LLM] Dev mode: Returning mock tags")
        return ["dev_tag_1", "dev_tag_2", "dev_tag_3"]

    client_info = get_random_client()
    if not client_info:
        return ["mock_tag_1", "mock_tag_2"]

    prompt = f"Extract 3-5 key tags from the following user demand. Return only the tags separated by commas.\n\nDemand: {text}\n\nTags:"
    
    try:
        client = client_info["client"]
        response = await client.chat.completions.create(
            model=client_info["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        return [tag.strip() for tag in content.strip().split(',')]
    except Exception as e:
        print(f"Error extracting tags: {e}")
        return ["mock_tag_1", "mock_tag_2"]


async def extract_tags_from_catalog(text: str, available_slugs: List[str]) -> List[str]:
    """Select matching tag slugs from a predefined catalog."""
    if settings.is_dev:
        import random as _rand
        sample_size = min(4, len(available_slugs))
        return _rand.sample(available_slugs, sample_size) if available_slugs else []

    client_info = get_random_client()
    if not client_info:
        return []

    slug_list = ", ".join(available_slugs)
    prompt = (
        f"From the following tag slugs, select ALL that apply to the text below. "
        f"Return ONLY the selected slugs as a JSON array of strings. "
        f"If none apply, return an empty array.\n\n"
        f"Available slugs: [{slug_list}]\n\n"
        f"Text: {text}\n\n"
        f"Selected slugs (JSON array):"
    )

    try:
        client = client_info["client"]
        response = await client.chat.completions.create(
            model=client_info["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("["):
            return json.loads(content)
        return [s.strip().strip('"').strip("'") for s in content.split(",") if s.strip()]
    except Exception as e:
        print(f"Error extracting catalog tags: {e}")
        return []


async def check_match_with_llm(user_a_demand: str, user_b_demand: str) -> bool:
    client_info = get_random_client()
    if not client_info:
        return True 

    prompt = f"""
    Determine if these two user demands are compatible for a match.
    
    User A: "{user_a_demand}"
    User B: "{user_b_demand}"
    
    Return ONLY "YES" if they are compatible (e.g. buyer/seller, dating match), or "NO" if they are not.
    """
    
    try:
        client = client_info["client"]
        response = await client.chat.completions.create(
            model=client_info["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        result = response.choices[0].message.content.strip().upper()
        return "YES" in result
    except Exception as e:
        print(f"Error checking match with LLM: {e}")
        return True 


async def judge_conversation(history: List[Dict[str, str]]) -> Dict[str, Any]:
    client_info = get_random_client()
    if not client_info:
        return {
            "verdict": "PENDING",
            "summary": "Mock summary",
            "reason": "Mock reason"
        }

    transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    prompt = f"""You are a strict judge evaluating a negotiation between two AI agents.

RULES FOR VERDICT:
- CONSENSUS: ONLY when BOTH agents have EXPLICITLY agreed on a concrete, specific outcome. 
  You must be able to point to exact quotes from BOTH sides confirming the deal.
  Vague pleasantries, "sounds good", or one-sided proposals do NOT count.
  Both agents must clearly state their acceptance of the SAME specific terms.
- DEADLOCK: The agents have fundamentally incompatible goals, have gone back and forth without progress, or one side has explicitly refused to continue.
- PENDING: The conversation is still ongoing — agents are still negotiating, exploring options, or have not yet both explicitly committed.

When in doubt, choose PENDING. Do NOT rush to CONSENSUS.

Transcript:
{transcript}

Output JSON:
{{
    "verdict": "CONSENSUS" | "DEADLOCK" | "PENDING",
    "summary": "Brief summary of the negotiation so far",
    "reason": "Specific evidence from the transcript supporting your verdict. For CONSENSUS, quote both agents' explicit agreement.",
    "final_outcome": "If CONSENSUS: a clear, concise description of what the two agents agreed on (e.g. price, terms, product, action items). If not CONSENSUS: null"
}}
"""
    
    try:
        client = client_info["client"]
        response = await client.chat.completions.create(
            model=client_info["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
            
    except Exception as e:
        print(f"Error judging conversation: {e}")
        return {"verdict": "PENDING", "summary": "Error", "reason": str(e)}
