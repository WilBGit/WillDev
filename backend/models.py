from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import Boolean, JSON, Date, func
from sqlalchemy.orm import validates
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import JSON
from backend.database import Base  # ✅ Base comes from database.py


# -----------------------------
# Core Tables
# -----------------------------

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    industry = Column(String, nullable=True)

    # Facebook integration
    facebook_page_id = Column(String, nullable=True)
    facebook_page_token = Column(Text, nullable=True)

    # Temporary page list (for post-login display)
    temp_facebook_pages = Column(JSON, nullable=True)

    # AI preferences
    preferences_json = Column(JSON, nullable=True)  # {"categories": [...], "ai_auto": true}
    model_name = Column(String, default="llama3")
    timezone = Column(String, default="America/Los_Angeles")
    post_time_hour = Column(Integer, default=17)
    post_time_minute = Column(Integer, default=0)

    # Relationships
    posts = relationship("Post", back_populates="client")

    def __repr__(self):
        return f"<Client id={self.id} name={self.name}>"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)

    status = Column(String, default="draft")  # draft, scheduled, posted, failed
    created_at = Column(DateTime, default=func.now())
    scheduled_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="posts")

    def __repr__(self):
        return f"<Post id={self.id} status={self.status}>"


# -----------------------------
# Subscription / Usage System
# -----------------------------

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    weekly_post_limit = Column(Integer, default=3)

    def __repr__(self):
        return f"<SubscriptionPlan name={self.name} limit={self.weekly_post_limit}>"


class ClientSubscription(Base):
    __tablename__ = "client_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)

    def __repr__(self):
        return f"<ClientSubscription client={self.client_id} plan={self.plan_id}>"


class WeeklyUsage(Base):
    __tablename__ = "weekly_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    posts_made = Column(Integer, default=0)

    @validates("posts_made")
    def validate_posts(self, key, value):
        return max(0, value)

    def __repr__(self):
        return f"<WeeklyUsage client={self.client_id} week={self.week_start} posts={self.posts_made}>"