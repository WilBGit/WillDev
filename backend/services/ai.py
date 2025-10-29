import httpx, os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = """You are a social media copywriter for a nail salon.
Return JSON with keys: caption (string), hashtags (string of up to 8 tags).
Tone: high-energy, friendly, IG style. Add one local/geo hint if provided.
"""

async def generate_caption_async(brief: str, categories: list[str] | None, city: str | None,
                                 model: str | None = None):
    model = model or DEFAULT_MODEL
    user_prompt = f"""Brief: {brief or "Create a short nail-salon promotional post."}
Categories: {", ".join(categories or [])}
City: {city or ""}
Return JSON only.
"""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": f"<system>{SYSTEM_PROMPT}</system>\n<user>{user_prompt}</user>",
            "stream": False,
            "temperature": 0.6,
        })
        r.raise_for_status()
        data = r.json()
        # Ollama returns {"response": "..."}
        import json
        try:
            return json.loads(data.get("response", "{}"))
        except Exception:
            # fallback safe shape
            return {"caption":"Fresh mani, fresh mood! 💅✨","hashtags":"#NailInspo #AzusaNails #SelfCare"}