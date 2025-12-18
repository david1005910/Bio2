from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.paper import Paper, Keyword, PaperKeyword
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/trends/keywords")
async def get_keyword_trends(
    keywords: Optional[str] = Query(None, description="Comma-separated keywords to track"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    aggregation: str = Query("monthly", pattern="^(weekly|monthly|yearly)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get keyword trends over time.

    Returns time-series data of keyword occurrences in papers.
    """
    # Parse dates
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = datetime.utcnow()

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = end_dt - timedelta(days=365)

    # Parse keywords
    keyword_list = keywords.split(",") if keywords else None

    # Get keyword counts
    if keyword_list:
        # Specific keywords
        trends = {}
        for kw in keyword_list:
            kw = kw.strip()
            result = await db.execute(
                select(
                    func.date_trunc(aggregation.rstrip("ly"), Paper.publication_date).label("period"),
                    func.count(Paper.pmid).label("count")
                )
                .join(PaperKeyword, Paper.pmid == PaperKeyword.paper_pmid)
                .join(Keyword, PaperKeyword.keyword_id == Keyword.id)
                .where(
                    Keyword.term.ilike(f"%{kw}%"),
                    Paper.publication_date >= start_dt,
                    Paper.publication_date <= end_dt
                )
                .group_by("period")
                .order_by("period")
            )
            trends[kw] = [
                {"period": str(row.period), "count": row.count}
                for row in result.fetchall()
            ]
    else:
        # Top keywords
        result = await db.execute(
            select(
                Keyword.term,
                func.count(PaperKeyword.paper_pmid).label("count")
            )
            .join(PaperKeyword, Keyword.id == PaperKeyword.keyword_id)
            .join(Paper, PaperKeyword.paper_pmid == Paper.pmid)
            .where(
                Paper.publication_date >= start_dt,
                Paper.publication_date <= end_dt
            )
            .group_by(Keyword.term)
            .order_by(func.count(PaperKeyword.paper_pmid).desc())
            .limit(20)
        )
        trends = {
            row.term: row.count
            for row in result.fetchall()
        }

    return {
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "aggregation": aggregation,
        "trends": trends
    }


@router.get("/topics/emerging")
async def get_emerging_topics(
    window_months: int = Query(6, ge=1, le=24),
    growth_threshold: float = Query(2.0, ge=1.0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Detect emerging research topics.

    Compares keyword frequency between recent and past periods.
    Returns keywords with significant growth.
    """
    end_date = datetime.utcnow()
    mid_date = end_date - timedelta(days=window_months * 30)
    start_date = mid_date - timedelta(days=window_months * 30)

    # Recent period counts
    recent_result = await db.execute(
        select(
            Keyword.term,
            func.count(PaperKeyword.paper_pmid).label("count")
        )
        .join(PaperKeyword, Keyword.id == PaperKeyword.keyword_id)
        .join(Paper, PaperKeyword.paper_pmid == Paper.pmid)
        .where(
            Paper.publication_date >= mid_date,
            Paper.publication_date <= end_date
        )
        .group_by(Keyword.term)
        .having(func.count(PaperKeyword.paper_pmid) >= 5)
    )
    recent_counts = {row.term: row.count for row in recent_result.fetchall()}

    # Past period counts
    past_result = await db.execute(
        select(
            Keyword.term,
            func.count(PaperKeyword.paper_pmid).label("count")
        )
        .join(PaperKeyword, Keyword.id == PaperKeyword.keyword_id)
        .join(Paper, PaperKeyword.paper_pmid == Paper.pmid)
        .where(
            Paper.publication_date >= start_date,
            Paper.publication_date < mid_date
        )
        .group_by(Keyword.term)
    )
    past_counts = {row.term: row.count for row in past_result.fetchall()}

    # Calculate growth rates
    emerging = []
    for term, recent_count in recent_counts.items():
        past_count = past_counts.get(term, 1)  # Avoid division by zero
        growth_rate = recent_count / past_count

        if growth_rate >= growth_threshold:
            emerging.append({
                "keyword": term,
                "recent_count": recent_count,
                "past_count": past_count,
                "growth_rate": round(growth_rate, 2)
            })

    # Sort by growth rate
    emerging.sort(key=lambda x: x["growth_rate"], reverse=True)

    return {
        "window_months": window_months,
        "growth_threshold": growth_threshold,
        "emerging_topics": emerging[:limit]
    }


@router.get("/stats")
async def get_database_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get database statistics.
    """
    # Total papers
    paper_count = await db.execute(select(func.count(Paper.pmid)))
    total_papers = paper_count.scalar()

    # Total keywords
    keyword_count = await db.execute(select(func.count(Keyword.id)))
    total_keywords = keyword_count.scalar()

    # Papers by year
    year_result = await db.execute(
        select(
            func.extract("year", Paper.publication_date).label("year"),
            func.count(Paper.pmid).label("count")
        )
        .where(Paper.publication_date.isnot(None))
        .group_by("year")
        .order_by("year")
    )
    papers_by_year = {
        int(row.year): row.count
        for row in year_result.fetchall()
        if row.year
    }

    # Top journals
    journal_result = await db.execute(
        select(
            Paper.journal,
            func.count(Paper.pmid).label("count")
        )
        .where(Paper.journal.isnot(None))
        .group_by(Paper.journal)
        .order_by(func.count(Paper.pmid).desc())
        .limit(10)
    )
    top_journals = [
        {"journal": row.journal, "count": row.count}
        for row in journal_result.fetchall()
    ]

    return {
        "total_papers": total_papers,
        "total_keywords": total_keywords,
        "papers_by_year": papers_by_year,
        "top_journals": top_journals
    }
