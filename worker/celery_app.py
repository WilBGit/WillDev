from celery import Celery
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "autoai",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,
    include=[
        "worker.tasks.posting",
        "worker.tasks.generate",
        "worker.tasks.publish",
    ],
)

celery.conf.timezone = "America/Los_Angeles"
celery.conf.beat_schedule = {
    "auto-publish-posts": {
        "task": "worker.tasks.publish.post_scheduled_posts",
        "schedule": 60 * 10,
    },
    "auto-schedule-daily-posts": {
        "task": "worker.tasks.posting.schedule_next_post",
        "schedule": 60 * 30,
    },
    
}
from celery.schedules import crontab
celery.conf.beat_schedule.update({
    "ai-daily-scheduler-5min": {
        "task": "worker.tasks.schedule.ai_daily_scheduler",
        "schedule": 60 * 5,
    },
})