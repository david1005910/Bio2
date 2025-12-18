from fastapi import APIRouter

from .auth import router as auth_router
from .search import router as search_router
from .chat import router as chat_router
from .papers import router as papers_router
from .recommendations import router as recommendations_router
from .analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat/RAG"])
api_router.include_router(papers_router, prefix="/papers", tags=["Papers"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
