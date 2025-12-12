import time
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.search import SearchRequest, SearchFilters, SearchResponse
from app.services.search import SemanticSearchService, get_search_service
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("", response_model=SearchResponse)
async def search_papers(
    q: str = Query(..., min_length=2, max_length=500, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    year_start: Optional[int] = Query(None, ge=1900, le=2100),
    year_end: Optional[int] = Query(None, ge=1900, le=2100),
    journals: Optional[str] = Query(None, description="Comma-separated journal names"),
    sort_by: str = Query("relevance", pattern="^(relevance|date|citations)$"),
    rerank: bool = Query(True, description="Apply reranking for better results"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Search papers using semantic search.

    - **q**: Natural language search query
    - **limit**: Number of results to return (1-100)
    - **offset**: Pagination offset
    - **year_start/year_end**: Filter by publication year range
    - **journals**: Filter by journal names (comma-separated)
    - **sort_by**: Sort results by relevance, date, or citations
    - **rerank**: Whether to apply cross-encoder reranking
    """
    start_time = time.time()

    # Build filters
    filters = SearchFilters(
        year_start=year_start,
        year_end=year_end,
        journals=journals.split(",") if journals else None,
        sort_by=sort_by
    )

    # Perform search
    search_service = get_search_service()
    results = await search_service.search(
        query=q,
        filters=filters,
        top_k=limit + offset,
        rerank=rerank,
        db=db
    )

    # Apply pagination
    paginated_results = results[offset:offset + limit]

    query_time_ms = int((time.time() - start_time) * 1000)

    return SearchResponse(
        results=paginated_results,
        total=len(results),
        page=offset // limit + 1 if limit > 0 else 1,
        query_time_ms=query_time_ms,
        query=q
    )


@router.post("", response_model=SearchResponse)
async def search_papers_advanced(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Advanced search with complex filters.

    Request body allows specifying multiple filter criteria.
    """
    start_time = time.time()

    search_service = get_search_service()
    results = await search_service.search(
        query=request.query,
        filters=request.filters,
        top_k=request.limit + request.offset,
        rerank=request.rerank,
        db=db
    )

    # Apply pagination
    paginated_results = results[request.offset:request.offset + request.limit]

    query_time_ms = int((time.time() - start_time) * 1000)

    return SearchResponse(
        results=paginated_results,
        total=len(results),
        page=request.offset // request.limit + 1 if request.limit > 0 else 1,
        query_time_ms=query_time_ms,
        query=request.query
    )
