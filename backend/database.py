from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# -------------------------------------------------------------------
# DATABASE URL
# -------------------------------------------------------------------
# Default: local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# -------------------------------------------------------------------
# SQLAlchemy Engine
# -------------------------------------------------------------------
# For SQLite, `check_same_thread=False` is required for async contexts.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# -------------------------------------------------------------------
# Session Factory
# -------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------------------------------------------------
# Base Model Class
# -------------------------------------------------------------------
Base = declarative_base()

# -------------------------------------------------------------------
# FastAPI Dependency - provides DB session per request
# -------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()