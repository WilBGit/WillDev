from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from backend.routers.generate import router as generate_router
from backend.routers.posts import router as posts_router
from backend.routers.facebook import router as facebook_router
from backend.routers.ai import router as ai_router


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router)
app.include_router(posts_router)
app.include_router(facebook_router)
app.include_router(ai_router)