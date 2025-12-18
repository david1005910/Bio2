# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bio-RAG is an AI-powered biomedical paper analysis platform using RAG (Retrieval-Augmented Generation) for semantic search, paper Q&A, and research analytics over scientific literature.

## Build and Run Commands

### Backend (FastAPI)
```bash
cd backend

# Install dependencies (use virtual environment)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Run Celery worker (requires Redis running)
celery -A app.workers.celery_app worker --loglevel=info

# Run Celery beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend (Next.js)
```bash
cd frontend

npm install
npm run dev          # Development server on port 3000
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript type checking
```

### Docker (Full Stack)
```bash
docker-compose up -d              # Start all services
docker-compose logs -f backend    # View backend logs
docker-compose down               # Stop all services
```

Services exposed: Frontend (3000), Backend API (8000), PostgreSQL (5432), Redis (6379), Flower monitoring (5555)

### Testing
```bash
cd backend
pytest                           # Run all tests
pytest -v                        # Verbose output
pytest tests/test_file.py        # Run single test file
pytest -k "test_name"            # Run tests matching pattern
pytest --cov=app                 # With coverage
```

## Architecture

```
Frontend (Next.js/React) → FastAPI Gateway → Services Layer → Data Layer
                                                ↓
                              ┌─────────────────┼─────────────────┐
                              │                 │                 │
                        SearchService     RAGService      RecommendationService
                              │                 │                 │
                              └─────────────────┼─────────────────┘
                                                ↓
                              ┌─────────────────┼─────────────────┐
                              │                 │                 │
                         PostgreSQL        ChromaDB           Redis
                        (metadata)        (vectors)          (cache)
```

### Backend Service Layer (`backend/app/services/`)
- `rag.py`: Core RAG pipeline - embeds question, vector search, reranks with cross-encoder, generates answer via OpenAI, validates citations
- `embedding.py`: PubMedBERT embeddings (768-dim), `TextChunker` for splitting papers (512 tokens, 50 overlap)
- `search.py`: Semantic search with optional reranking
- `pubmed.py`: PubMed API integration for paper collection
- `recommendation.py`: Content + citation similarity (70/30 hybrid)

### API Routes (`backend/app/api/v1/`)
- `/auth/*` - JWT authentication (register, login, refresh)
- `/search` - Semantic paper search
- `/chat/query` - RAG Q&A endpoint
- `/papers/*` - Paper CRUD, library management
- `/recommendations/*` - Similar papers, trending topics
- `/analytics/*` - Keyword trends, emerging topics

### Frontend Structure (`frontend/src/`)
- `services/api.ts` - Centralized API client with auth interceptors
- `pages/` - Next.js pages (chat, search, trends, library, login, register)
- `components/` - Reusable UI (ChatInterface, SearchBar, PaperCard, Layout)
- `hooks/useAuth.ts` - Authentication state management

## Key Implementation Details

### RAG Pipeline (backend/app/services/rag.py)
1. Embed question with PubMedBERT
2. Vector search (retrieve 2x candidates if reranking)
3. Rerank with `cross-encoder/ms-marco-MiniLM-L-12-v2`
4. Build context with PMID citations
5. Generate answer via GPT-4
6. Validate: check cited PMIDs exist in sources, calculate confidence

### Embedding Generation (backend/app/services/embedding.py)
- Uses singleton pattern to avoid reloading model
- Model: `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract`
- Outputs 768-dimensional L2-normalized vectors
- `TextChunker`: Fixed-size (512 tokens) or section-based chunking

### Response Format
RAG responses must cite sources as `[PMID: xxxxx]` and only use information from retrieved context. The validation layer checks that all cited PMIDs exist in the retrieved sources.

## Environment Variables

Required in `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/biorag
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
PUBMED_API_KEY=...
JWT_SECRET_KEY=your-secret-key
```

## Configuration

Key settings in `backend/app/core/config.py`:
- `LLM_MODEL`: gpt-4-turbo-preview
- `EMBEDDING_MODEL`: microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract
- `RERANK_MODEL`: cross-encoder/ms-marco-MiniLM-L-12-v2
- `CHUNK_SIZE`: 512 tokens
- `CHUNK_OVERLAP`: 50 tokens
- Rate limits: Search 60/min, RAG 20/min, General 100/min
