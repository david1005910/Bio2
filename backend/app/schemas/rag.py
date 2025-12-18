from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class SourceInfo(BaseModel):
    pmid: str
    title: str
    relevance: float = Field(..., ge=0, le=1)
    excerpt: str
    section: Optional[str] = None
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None


class RAGRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)
    session_id: Optional[str] = None
    max_sources: int = Field(5, ge=1, le=10)
    temperature: float = Field(0.1, ge=0, le=1)
    include_citations: bool = True
    filters: Optional[dict] = None


class RAGResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    confidence: float = Field(..., ge=0, le=1)
    response_time_ms: int
    session_id: Optional[str] = None
    chunks_used: int


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime
    sources: Optional[List[SourceInfo]] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    last_updated: datetime


class ValidationResult(BaseModel):
    is_valid: bool
    confidence: float
    cited_sources: List[str]
    warnings: Optional[List[str]] = None
