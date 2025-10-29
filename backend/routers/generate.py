from fastapi import APIRouter
import httpx
import hashlib
import os

# ------------------------------
# Router & Config
# ------------------------------
router = APIRouter(prefix="/generate", tags=["generate"])

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def hash_text(s: str) -> str:
    return hashlib.sha256(s.strip().lower().encode()).hexdigest()

# ------------------------------
# Core Ollama Chat Function
# ------------------------------
async def ollama_chat(messages):
    """
    Uses Ollama's /api/chat format (correct for your version).
    """
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "temperature": 0.6,
                "stream": False
            }
        )
        r.raise_for_status()
        data = r.json()
        # Response structure: { "message": { "content": "..." } }
        return data["message"]["content"].strip()

# ------------------------------
# Caption Generator Endpoint
# ------------------------------
@router.post("/caption")
async def gen_caption(payload: dict):
    business = payload.get("businessName", "")
    city = payload.get("city", "")
    vibe = payload.get("vibe", "")
    services = payload.get("services", "")

    system_prompt = (
        "You are a calm, elegant social media caption writer for local beauty businesses. "
        "Your tone is gentle, confident, and warm — never hype or salesy. "
        "Always include the city name naturally, and keep captions short (1–3 lines). "
        "Do not use emojis unless the brand vibe explicitly encourages them. "
    )

    user_prompt = (
        f"Business Name: {business}\n"
        f"City: {city}\n"
        f"Brand Vibe: {vibe}\n"
        f"Services: {services}\n\n"
        f"Write one caption."
    )

    caption = await ollama_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    return {"caption": caption, "hash": hash_text(caption)}

# ------------------------------
# Hashtag Generator Endpoint
# ------------------------------
@router.post("/hashtags")
async def gen_hashtags(payload: dict):
    city = payload.get("city", "")
    services = payload.get("services", "")

    system_prompt = "You generate clean, relevant, local discovery hashtags. No filler."
    user_prompt = f"Generate 6-10 hashtags for a {services} business in {city}. One line only."

    hashtags = await ollama_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    return {"hashtags": hashtags}