from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models import Post        # ✅ CORRECT IMPORT
from backend.database import get_db    # ✅ CORRECT IMPORT

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/{client_id}")
def get_posts(client_id: int, db: Session = Depends(get_db)):
    posts = (
        db.query(Post)
        .filter(Post.client_id == client_id)
        .order_by(Post.created_at.desc())
        .all()
    )

    return [
        {
            "id": p.id,
            "caption": p.caption,
            "hashtags": p.hashtags,
            "created_at": p.created_at.isoformat(),
        }
        for p in posts
    ]