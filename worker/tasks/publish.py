import os
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from celery import shared_task
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.database import DATABASE_URL
from backend.models import Client, Post, SubscriptionPlan, ClientSubscription, WeeklyUsage
from backend.services.ai import generate_caption_async

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def week_start_today():
    today = date.today()
    return today - timedelta(days=today.weekday())  # Monday

def get_weekly_limit(db, client_id: int) -> int:
    sub = db.query(ClientSubscription).filter_by(client_id=client_id).first()
    if not sub:
        plan = db.query(SubscriptionPlan).filter_by(name="free").first()
    else:
        plan = db.query(SubscriptionPlan).filter_by(id=sub.plan_id).first()
    return plan.weekly_post_limit if plan else 3

@shared_task
def ai_daily_scheduler():
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        for c in clients:
            # time check (local)
            tz = ZoneInfo(c.timezone or "America/Los_Angeles")
            now_local = datetime.now(tz)
            target = now_local.replace(hour=c.post_time_hour or 17,
                                       minute=c.post_time_minute or 0,
                                       second=0, microsecond=0)
            if now_local < target:
                continue  # not time yet

            # weekly usage
            ws = week_start_today()
            usage = (db.query(WeeklyUsage)
                       .filter(WeeklyUsage.client_id==c.id,
                               WeeklyUsage.week_start==ws)
                       .first())
            if not usage:
                usage = WeeklyUsage(client_id=c.id, week_start=ws, posts_made=0)
                db.add(usage); db.commit()

            limit = get_weekly_limit(db, c.id)
            if usage.posts_made >= limit:
                continue  # quota reached

            # if there is already a scheduled/post due today, skip
            existing = (db.query(Post)
                          .filter(Post.client_id==c.id,
                                  Post.status.in_(["scheduled","posted"]))
                          .filter(func.date(Post.scheduled_at) == now_local.date())
                          .first())
            if existing:
                continue

            # pick a draft or generate new via AI
            post = (db.query(Post)
                      .filter(Post.client_id==c.id, Post.status=="draft")
                      .order_by(Post.created_at.asc())
                      .first())

            if not post:
                # generate via AI (auto mode or fallback brief="")
                cats = (c.preferences_json or {}).get("categories", [])
                res = httpx_run_generate(c.id, cats, c.city, c.model_name)
                caption = res.get("caption") or "New set just dropped 💥💅"
                hashtags = res.get("hashtags") or "#NailInspo"
                post = Post(client_id=c.id, caption=caption, hashtags=hashtags, status="draft")
                db.add(post); db.commit()

            # schedule it for “now” (publisher runs every X minutes)
            post.status = "scheduled"
            post.scheduled_at = datetime.utcnow()
            db.add(post); db.commit()
            # record usage immediately (to avoid double-posting on re-run)
            usage.posts_made += 1
            db.add(usage); db.commit()
    finally:
        db.close()

def httpx_run_generate(client_id, cats, city, model):
    # Small wrapper to call the same async generator in a sync Celery context
    import asyncio
    from backend.services.ai import generate_caption_async
    return asyncio.run(generate_caption_async("",
        categories=cats, city=city, model=model))