from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.domain.models import Base
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./usuarios.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def init_db():
    Base.metadata.create_all(bind=engine)
