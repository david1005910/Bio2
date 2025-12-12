from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.recommendation import PaperRecommender, get_recommender
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/similar/{pmid}")
async def get_similar_papers(
    pmid: str,
    limit: int = Query(5, ge=1, le=20),
    method: str = Query("hybrid", pattern="^(content|citation|hybrid)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get similar paper recommendations.

    Methods:
    - **content**: Based on text/embedding similarity
    - **citation**: Based on citation network analysis
    - **hybrid**: Combined approach (recommended)
    """
    recommender = get_recommender()

    recommendations = await recommender.recommend_similar_papers(
        pmid=pmid,
        top_k=limit,
        method=method,
        db=db
    )

    return {
        "source_pmid": pmid,
        "method": method,
        "recommendations": recommendations
    }


@router.get("/trending")
async def get_trending_papers(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get trending papers based on recent activity.

    - **days**: Time window to consider (default: 30 days)
    - **limit**: Number of papers to return
    """
    recommender = get_recommender()

    trending = await recommender.get_trending_papers(
        days=days,
        top_k=limit,
        db=db
    )

    return {
        "period_days": days,
        "papers": trending
    }


@router.get("/personalized")
async def get_personalized_recommendations(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized recommendations based on user's saved papers.

    Requires authentication. Returns papers similar to user's library.
    """
    if not current_user:
        return {"recommendations": [], "message": "Login for personalized recommendations"}

    from sqlalchemy import select
    from app.models.user import UserSavedPaper

    # Get user's saved papers
    result = await db.execute(
        select(UserSavedPaper.paper_pmid)
        .where(UserSavedPaper.user_id == current_user.id)
        .limit(10)
    )
    saved_pmids = [row[0] for row in result.fetchall()]

    if not saved_pmids:
        return {
            "recommendations": [],
            "message": "Save some papers to get personalized recommendations"
        }

    # Get recommendations based on saved papers
    recommender = get_recommender()
    all_recs = []

    for pmid in saved_pmids[:5]:  # Use top 5 saved papers
        recs = await recommender.recommend_similar_papers(
            pmid=pmid,
            top_k=3,
            method="content",
            db=db
        )
        all_recs.extend(recs)

    # Deduplicate and sort by score
    seen = set(saved_pmids)  # Exclude saved papers
    unique_recs = []

    for rec in sorted(all_recs, key=lambda x: x["similarity_score"], reverse=True):
        if rec["pmid"] not in seen:
            seen.add(rec["pmid"])
            unique_recs.append(rec)
            if len(unique_recs) >= limit:
                break

    return {
        "based_on_papers": len(saved_pmids),
        "recommendations": unique_recs
    }
