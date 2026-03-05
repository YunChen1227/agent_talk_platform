from typing import List, Dict, Any, Optional
import json
import random
from openai import AsyncOpenAI
import google.generativeai as genai
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

    # Gemini
    # if settings.GEMINI_API_KEY:
    #     try:
    #         genai.configure(api_key=settings.GEMINI_API_KEY)
    #         valid_clients["gemini"] = {"client": genai, "model": "gemini-2.0-flash"} 
    #         print("Gemini API key configured.")
    #     except Exception as e:
    #         print(f"Gemini validation failed: {e}")

    print(f"Validation complete. Valid providers: {list(valid_clients.keys())}")


def get_random_client() -> Optional[Dict[str, Any]]:
    if not valid_clients:
        return None
    provider = random.choice(list(valid_clients.keys()))
    return {"provider": provider, **valid_clients[provider]}


async def get_embedding(text: str) -> List[float]:
    if "openai" in valid_clients:
        client = valid_clients["openai"]["client"]
        try:
            response = await client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding from OpenAI: {e}")
    
    # Mock embedding
    return [random.random() for _ in range(1536)]


async def extract_tags(text: str) -> List[str]:
    client_info = get_random_client()
    if not client_info:
        return ["mock_tag_1", "mock_tag_2"]

    prompt = f"Extract 3-5 key tags from the following user demand. Return only the tags separated by commas.\n\nDemand: {text}\n\nTags:"
    
    try:
        if client_info["provider"] == "gemini":
            model = genai.GenerativeModel(client_info["model"])
            response = await model.generate_content_async(prompt)
            content = response.text
        else:
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
        if client_info["provider"] == "gemini":
            model = genai.GenerativeModel(client_info["model"])
            response = await model.generate_content_async(prompt)
            result = response.text.strip().upper()
        else:
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
    prompt = f"""
    Analyze the following conversation between two agents.
    Determine if they have reached a CONSENSUS (agreement to connect users), a DEADLOCK (no match possible), or if the conversation is still PENDING (ongoing).
    
    Transcript:
    {transcript}
    
    Output JSON format:
    {{
        "verdict": "CONSENSUS" | "DEADLOCK" | "PENDING",
        "summary": "Brief summary of the negotiation",
        "reason": "Reason for the verdict"
    }}
    """
    
    try:
        if client_info["provider"] == "gemini":
            model = genai.GenerativeModel(client_info["model"])
            response = await model.generate_content_async(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        else:
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
