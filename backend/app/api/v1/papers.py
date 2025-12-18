from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.paper import Paper, PaperAuthor, Author, PaperKeyword, Keyword
from app.models.user import User, UserSavedPaper
from app.schemas.paper import PaperResponse, PaperListResponse, PaperCreate
from app.api.deps import get_current_user, get_current_active_user


router = APIRouter()


@router.get("", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    journal: Optional[str] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """List papers with pagination and filters"""
    # Build query
    query = select(Paper)

    if journal:
        query = query.where(Paper.journal.ilike(f"%{journal}%"))

    if year:
        query = query.where(func.extract("year", Paper.publication_date) == year)

    # Count total
    count_query = select(func.count()).select_from(Paper)
    if journal:
        count_query = count_query.where(Paper.journal.ilike(f"%{journal}%"))
    if year:
        count_query = count_query.where(func.extract("year", Paper.publication_date) == year)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Paper.publication_date.desc())

    result = await db.execute(query)
    papers = result.scalars().all()

    # Format response
    paper_responses = []
    for paper in papers:
        # Get authors
        authors = []
        for pa in paper.authors:
            authors.append(pa.author.name)

        # Get keywords
        keywords = []
        for pk in paper.keywords:
            keywords.append(pk.keyword.term)

        paper_responses.append(PaperResponse(
            pmid=paper.pmid,
            title=paper.title,
            abstract=paper.abstract,
            doi=paper.doi,
            journal=paper.journal,
            publication_date=paper.publication_date,
            pdf_url=paper.pdf_url,
            citation_count=paper.citation_count,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
            authors=authors,
            keywords=keywords
        ))

    return PaperListResponse(
        papers=paper_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=offset + len(papers) < total
    )


@router.get("/{pmid}", response_model=PaperResponse)
async def get_paper(
    pmid: str,
    db: AsyncSession = Depends(get_db)
):
    """Get paper by PMID"""
    result = await db.execute(
        select(Paper).where(Paper.pmid == pmid)
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    # Get authors
    authors = [pa.author.name for pa in paper.authors]

    # Get keywords
    keywords = [pk.keyword.term for pk in paper.keywords]

    return PaperResponse(
        pmid=paper.pmid,
        title=paper.title,
        abstract=paper.abstract,
        doi=paper.doi,
        journal=paper.journal,
        publication_date=paper.publication_date,
        pdf_url=paper.pdf_url,
        citation_count=paper.citation_count,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        authors=authors,
        keywords=keywords
    )


@router.post("/{pmid}/save")
async def save_paper(
    pmid: str,
    notes: Optional[str] = None,
    tags: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Save paper to user's library"""
    # Check paper exists
    result = await db.execute(
        select(Paper).where(Paper.pmid == pmid)
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    # Check if already saved
    existing = await db.execute(
        select(UserSavedPaper).where(
            UserSavedPaper.user_id == current_user.id,
            UserSavedPaper.paper_pmid == pmid
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paper already saved"
        )

    # Save
    saved_paper = UserSavedPaper(
        user_id=current_user.id,
        paper_pmid=pmid,
        notes=notes,
        tags=tags
    )

    db.add(saved_paper)
    await db.commit()

    return {"message": "Paper saved successfully"}


@router.delete("/{pmid}/save")
async def unsave_paper(
    pmid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove paper from user's library"""
    result = await db.execute(
        select(UserSavedPaper).where(
            UserSavedPaper.user_id == current_user.id,
            UserSavedPaper.paper_pmid == pmid
        )
    )
    saved_paper = result.scalar_one_or_none()

    if not saved_paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not in library"
        )

    await db.delete(saved_paper)
    await db.commit()

    return {"message": "Paper removed from library"}


@router.get("/library/saved", response_model=List[PaperResponse])
async def get_saved_papers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's saved papers"""
    result = await db.execute(
        select(UserSavedPaper)
        .where(UserSavedPaper.user_id == current_user.id)
        .order_by(UserSavedPaper.saved_at.desc())
    )
    saved_papers = result.scalars().all()

    papers = []
    for sp in saved_papers:
        paper = sp.paper
        authors = [pa.author.name for pa in paper.authors]
        keywords = [pk.keyword.term for pk in paper.keywords]

        papers.append(PaperResponse(
            pmid=paper.pmid,
            title=paper.title,
            abstract=paper.abstract,
            doi=paper.doi,
            journal=paper.journal,
            publication_date=paper.publication_date,
            pdf_url=paper.pdf_url,
            citation_count=paper.citation_count,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
            authors=authors,
            keywords=keywords
        ))

    return papers
