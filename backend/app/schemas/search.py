from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class SearchFilters(BaseModel):
    year_start: Optional[int] = Field(None, ge=1900, le=2100)
    year_end: Optional[int] = Field(None, ge=1900, le=2100)
    journals: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    sort_by: str = Field("relevance", pattern="^(relevance|date|citations)$")

    @validator("year_end")
    def year_end_must_be_after_start(cls, v, values):
        if v and values.get("year_start") and v < values["year_start"]:
            raise ValueError("year_end must be >= year_start")
        return v


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    filters: Optional[SearchFilters] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
    include_abstract: bool = True
    rerank: bool = True

    @validator("query")
    def sanitize_query(cls, v):
        # Basic sanitization
        v = v.replace(";", "").replace("<", "").replace(">", "")
        return v.strip()


class SearchResult(BaseModel):
    pmid: str
    title: str
    abstract: Optional[str] = None
    relevance_score: float = Field(..., ge=-100, le=100)  # Cross-encoder scores can exceed 0-1
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    authors: List[str] = []
    citation_count: int = 0
    keywords: List[str] = []
    matched_chunks: Optional[List[str]] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    query_time_ms: int
    query: str
