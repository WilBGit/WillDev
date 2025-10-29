import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.models import Post, Client
from backend.database import DATABASE_URL
from worker.celery_app import celery

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery.task
def generate_monthly_posts(client_id: int):
    """
    Example placeholder task — generates one sample draft post.
    Later we integrate your real AI generate logic.
    """
    db = SessionLocal()

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        db.close()
        return

    sample_caption = f"New style day at {client.name} in {client.city} ✨"
    new_post = Post(
        client_id=client_id,
        caption=sample_caption,
        hashtags="#nails #nailart #selfcare",
        status="draft",
        created_at=datetime.utcnow()
    )

    db.add(new_post)
    db.commit()
    db.close()

    print(f"[OK] Generated sample post for client {client_id}")