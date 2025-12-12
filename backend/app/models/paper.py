from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Integer, Date, ForeignKey, DateTime, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Paper(Base):
    __tablename__ = "papers"

    pmid: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    journal: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    authors: Mapped[List["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="paper", cascade="all, delete-orphan"
    )
    keywords: Mapped[List["PaperKeyword"]] = relationship(
        "PaperKeyword", back_populates="paper", cascade="all, delete-orphan"
    )
    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk", back_populates="paper", cascade="all, delete-orphan"
    )
    citing_papers: Mapped[List["Citation"]] = relationship(
        "Citation",
        foreign_keys="Citation.cited_pmid",
        back_populates="cited_paper",
    )
    cited_papers: Mapped[List["Citation"]] = relationship(
        "Citation",
        foreign_keys="Citation.citing_pmid",
        back_populates="citing_paper",
    )


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    affiliation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    papers: Mapped[List["PaperAuthor"]] = relationship(
        "PaperAuthor", back_populates="author"
    )


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    paper_pmid: Mapped[str] = mapped_column(
        String(20), ForeignKey("papers.pmid"), primary_key=True
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("authors.id"), primary_key=True
    )
    author_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="authors")
    author: Mapped["Author"] = relationship("Author", back_populates="papers")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'mesh', 'author_keyword', etc.

    # Relationships
    papers: Mapped[List["PaperKeyword"]] = relationship(
        "PaperKeyword", back_populates="keyword"
    )


class PaperKeyword(Base):
    __tablename__ = "paper_keywords"

    paper_pmid: Mapped[str] = mapped_column(
        String(20), ForeignKey("papers.pmid"), primary_key=True
    )
    keyword_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("keywords.id"), primary_key=True
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="keywords")
    keyword: Mapped["Keyword"] = relationship("Keyword", back_populates="papers")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_pmid: Mapped[str] = mapped_column(
        String(20), ForeignKey("papers.pmid"), nullable=False
    )
    section: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'abstract', 'introduction', etc.
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="chunks")


class Citation(Base):
    __tablename__ = "citations"

    citing_pmid: Mapped[str] = mapped_column(
        String(20), ForeignKey("papers.pmid"), primary_key=True
    )
    cited_pmid: Mapped[str] = mapped_column(
        String(20), ForeignKey("papers.pmid"), primary_key=True
    )

    # Relationships
    citing_paper: Mapped["Paper"] = relationship(
        "Paper", foreign_keys=[citing_pmid], back_populates="cited_papers"
    )
    cited_paper: Mapped["Paper"] = relationship(
        "Paper", foreign_keys=[cited_pmid], back_populates="citing_papers"
    )
