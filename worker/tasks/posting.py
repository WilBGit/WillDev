
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.models import Post, Client
from backend.database import DATABASE_URL
from worker.celery_app import celery

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def choose_post_time(city: str) -> int:
    """
    Returns the local best posting hour (24h format).
    Simple defaults; later we can A/B test.
    """
    return 11  # 11:00 AM local — universal salon engagement sweet spot

@celery.task
def schedule_next_post():
    db = SessionLocal()

    # Get all clients with unscheduled draft posts
    clients = db.query(Client).all()

    for client in clients:
        # Find next unscheduled post
        post = (
            db.query(Post)
            .filter(Post.client_id == client.id, Post.status == "draft")
            .order_by(Post.created_at.asc())
            .first()
        )

        if not post:
            continue  # nothing to schedule

        # Determine optimal time
        post_hour = choose_post_time(client.city)
        today = datetime.now().date()
        scheduled = datetime(today.year, today.month, today.day, post_hour)

        # If it's already past this time today → schedule tomorrow
        if scheduled < datetime.now():
            scheduled += timedelta(days=1)

        post.scheduled_at = scheduled
        post.status = "scheduled"
        db.add(post)

    db.commit()
    db.close()