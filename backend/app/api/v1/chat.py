import time
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.rag import RAGRequest, RAGResponse, SourceInfo
from app.services.rag import RAGService, ConversationManager, get_rag_service
from app.api.deps import get_current_user, get_current_active_user
from app.models.user import User


router = APIRouter()

# Conversation manager instance
conversation_manager = ConversationManager()


@router.post("/query", response_model=RAGResponse)
async def chat_query(
    request: RAGRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Ask a question and get an AI-generated answer based on research papers.

    The RAG system will:
    1. Search for relevant paper chunks
    2. Re-rank results for relevance
    3. Generate an answer using GPT-4
    4. Validate citations against sources

    Response includes:
    - Generated answer with citations
    - Source papers used
    - Confidence score
    """
    start_time = time.time()

    # Get or create session ID
    session_id = request.session_id or str(uuid4())

    # Get RAG service
    rag_service = get_rag_service()

    try:
        # Query RAG system
        result = await rag_service.query(
            question=request.question,
            top_k=request.max_sources,
            rerank=True,
            temperature=request.temperature,
            filter_dict=request.filters
        )

        # Store in conversation history
        conversation_manager.add_message(session_id, "user", request.question)
        conversation_manager.add_message(
            session_id,
            "assistant",
            result.answer,
            sources=[
                {"pmid": s["pmid"], "title": s["title"]}
                for s in result.sources
            ]
        )

        response_time_ms = int((time.time() - start_time) * 1000)

        # Format sources
        sources = [
            SourceInfo(
                pmid=s["pmid"],
                title=s["title"],
                relevance=s["relevance"],
                excerpt=s["excerpt"],
                section=s.get("section")
            )
            for s in result.sources
        ]

        return RAGResponse(
            answer=result.answer,
            sources=sources,
            confidence=result.confidence,
            response_time_ms=response_time_ms,
            session_id=session_id,
            chunks_used=len(result.chunks_used)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get conversation history for a session"""
    history = conversation_manager.get_history(session_id)

    if not history:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return {
        "session_id": session_id,
        "messages": history
    }


@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Clear conversation history for a session"""
    conversation_manager.clear_history(session_id)
    return {"message": "History cleared"}


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.

    Send JSON messages:
    {
        "question": "Your question here",
        "session_id": "optional-session-id"
    }

    Receive streaming responses:
    - {"type": "chunk", "content": "..."} - Partial answer
    - {"type": "complete", "sources": [...]} - Final with sources
    """
    await websocket.accept()

    rag_service = get_rag_service()
    session_id = str(uuid4())

    try:
        while True:
            # Receive question
            data = await websocket.receive_json()
            question = data.get("question", "")

            if not question:
                await websocket.send_json({
                    "type": "error",
                    "content": "Question is required"
                })
                continue

            session_id = data.get("session_id", session_id)

            # Store user message
            conversation_manager.add_message(session_id, "user", question)

            # Stream response
            full_answer = ""
            async for chunk in rag_service.stream_response(question):
                full_answer += chunk
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })

            # Get sources for the answer
            question_embedding = rag_service.embedding_generator.encode(question)
            search_results = rag_service.vector_store.search(
                query_embedding=question_embedding,
                top_k=5
            )

            sources = [
                {
                    "pmid": r["metadata"].get("pmid"),
                    "title": r["metadata"].get("title"),
                    "relevance": r.get("similarity", 0)
                }
                for r in search_results
            ]

            # Store assistant message
            conversation_manager.add_message(
                session_id,
                "assistant",
                full_answer,
                sources=sources
            )

            # Send completion
            await websocket.send_json({
                "type": "complete",
                "sources": sources,
                "session_id": session_id
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
        except Exception:
            pass
