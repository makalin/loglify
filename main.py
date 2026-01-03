from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from database import init_db, get_db, LogEntry
from models import LogEntryCreate, LogEntryResponse, QueryRequest
from config import settings

app = FastAPI(title="Loglify API", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    return {"message": "Loglify API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/logs", response_model=LogEntryResponse)
async def create_log(entry: LogEntryCreate, db: Session = Depends(get_db)):
    """Create a new log entry"""
    db_entry = LogEntry(
        source=entry.source,
        raw_text=entry.raw_text,
        action=entry.action,
        project=entry.project,
        duration=entry.duration,
        tags=entry.tags,
        metadata=entry.metadata
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.get("/api/logs", response_model=List[LogEntryResponse])
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get log entries with optional filtering"""
    query = db.query(LogEntry)
    
    if source:
        query = query.filter(LogEntry.source == source)
    
    if start_date:
        query = query.filter(LogEntry.timestamp >= start_date)
    
    if end_date:
        query = query.filter(LogEntry.timestamp <= end_date)
    
    entries = query.order_by(desc(LogEntry.timestamp)).offset(skip).limit(limit).all()
    return entries


@app.get("/api/logs/stats")
async def get_stats(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get statistics for the last N days"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    total_logs = db.query(func.count(LogEntry.id)).filter(
        LogEntry.timestamp >= start_date
    ).scalar()
    
    total_duration = db.query(func.sum(LogEntry.duration)).filter(
        LogEntry.timestamp >= start_date,
        LogEntry.duration.isnot(None)
    ).scalar() or 0
    
    logs_by_source = db.query(
        LogEntry.source,
        func.count(LogEntry.id)
    ).filter(
        LogEntry.timestamp >= start_date
    ).group_by(LogEntry.source).all()
    
    logs_by_action = db.query(
        LogEntry.action,
        func.count(LogEntry.id)
    ).filter(
        LogEntry.timestamp >= start_date
    ).group_by(LogEntry.action).order_by(desc(func.count(LogEntry.id))).limit(10).all()
    
    return {
        "total_logs": total_logs,
        "total_duration_minutes": total_duration,
        "total_duration_hours": round(total_duration / 60, 2),
        "logs_by_source": {source: count for source, count in logs_by_source},
        "top_actions": {action: count for action, count in logs_by_action}
    }


@app.post("/api/query")
async def query_logs(request: QueryRequest, db: Session = Depends(get_db)):
    """Query logs using natural language (requires LLM)"""
    from llm_parser import LLMParser
    
    # Get relevant logs
    query = db.query(LogEntry)
    
    if request.start_date:
        query = query.filter(LogEntry.timestamp >= request.start_date)
    
    if request.end_date:
        query = query.filter(LogEntry.timestamp <= request.end_date)
    
    logs = query.order_by(desc(LogEntry.timestamp)).limit(100).all()
    
    # Convert to dict format for LLM
    logs_dict = [
        {
            "action": log.action,
            "project": log.project,
            "duration": log.duration,
            "timestamp": log.timestamp.isoformat(),
            "tags": log.tags
        }
        for log in logs
    ]
    
    parser = LLMParser()
    answer = parser.answer_query(request.query, logs_dict)
    
    return {"query": request.query, "answer": answer}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

