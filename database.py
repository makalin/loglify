from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()


class LogEntry(Base):
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, index=True)  # 'telegram', 'cli', 'github', etc.
    raw_text = Column(Text, nullable=True)
    action = Column(String, index=True)
    project = Column(String, nullable=True)
    duration = Column(Float, nullable=True)  # in minutes
    tags = Column(JSON, nullable=True)  # list of strings
    metadata = Column(JSON, nullable=True)  # additional structured data
    created_at = Column(DateTime, default=datetime.utcnow)


# Create engine and session
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

