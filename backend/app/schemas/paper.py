from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class AuthorResponse(BaseModel):
    id: int
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class KeywordResponse(BaseModel):
    id: int
    term: str
    type: Optional[str] = None

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: UUID
    paper_pmid: str
    section: Optional[str] = None
    text: str
    chunk_index: int
    token_count: Optional[int] = None

    class Config:
        from_attributes = True


class PaperBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=1000)
    abstract: Optional[str] = None
    doi: Optional[str] = Field(None, max_length=100)
    journal: Optional[str] = Field(None, max_length=255)
    publication_date: Optional[datetime] = None
    pdf_url: Optional[str] = None


class PaperCreate(PaperBase):
    pmid: str = Field(..., min_length=1, max_length=20)
    full_text: Optional[str] = None
    authors: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    mesh_terms: Optional[List[str]] = None


class PaperUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=1000)
    abstract: Optional[str] = None
    full_text: Optional[str] = None
    doi: Optional[str] = Field(None, max_length=100)
    journal: Optional[str] = Field(None, max_length=255)
    publication_date: Optional[datetime] = None
    citation_count: Optional[int] = None
    pdf_url: Optional[str] = None


class PaperResponse(PaperBase):
    pmid: str
    citation_count: int = 0
    created_at: datetime
    updated_at: datetime
    authors: List[str] = []
    keywords: List[str] = []

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
