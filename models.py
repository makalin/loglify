from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LogEntryCreate(BaseModel):
    source: str
    raw_text: Optional[str] = None
    action: str
    project: Optional[str] = None
    duration: Optional[float] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class LogEntryResponse(BaseModel):
    id: int
    timestamp: datetime
    source: str
    raw_text: Optional[str]
    action: str
    project: Optional[str]
    duration: Optional[float]
    tags: Optional[List[str]]
    metadata: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

