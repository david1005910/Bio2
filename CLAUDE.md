# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bio-RAG (Biomedical Research AI-Guided Analytics) is an AI-powered biomedical paper analysis platform that uses RAG (Retrieval-Augmented Generation) to help researchers quickly extract insights from scientific literature. The platform provides semantic search, paper Q&A, similar paper recommendations, and research trend analysis.

## Technology Stack

### Backend
- **Python 3.11+** with **FastAPI** for API server
- **Celery** with **Redis** for async task processing
- **LangChain** for RAG orchestration
- **PubMedBERT** (microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract) for domain-specific embeddings

### Frontend
- **React.js 18.2+** with **TypeScript 5.0+**
- **TailwindCSS** for styling
- **Recharts** for data visualization
- **React Query** for state management

### Databases
- **PostgreSQL 15+** for relational data (paper metadata, users, query logs)
- **ChromaDB** for vector storage (MVP phase)
- **FAISS** for large-scale vector search (production scale)
- **Redis** for caching and message queue

### External APIs
- **PubMed E-utilities API** for paper metadata collection
- **OpenAI GPT-4** for LLM responses

## Architecture Overview

```
Client Layer (React.js)
    ↓ HTTPS
API Gateway (FastAPI)
    ↓
┌─────────────┬─────────────┬─────────────┐
│ Search      │ RAG         │ Analytics   │
│ Service     │ Service     │ Service     │
└─────────────┴─────────────┴─────────────┘
    ↓
┌─────────────┬─────────────┬─────────────┐
│ Data        │ Embedding   │ Batch       │
│ Collector   │ Generator   │ Processor   │
└─────────────┴─────────────┴─────────────┘
    ↓
┌─────────────┬─────────────┬─────────────┐
│ PostgreSQL  │ Vector DB   │ S3/Object   │
│ (Metadata)  │ (ChromaDB)  │ Storage     │
└─────────────┴─────────────┴─────────────┘
```

## Key Components

### Data Collection Module
- `PubMedCollector`: Fetches paper metadata from PubMed API (rate limit: 10 req/sec with API key)
- `PDFProcessor`: Extracts and cleans text from PDFs, splits into sections (abstract, methods, results, etc.)
- Batch jobs run daily at UTC 02:00 via Celery Beat

### Embedding Module
- Uses PubMedBERT for 768-dimensional embeddings
- Text chunking: Fixed-size (512 tokens with 50-token overlap) or section-based for papers
- Chunk metadata includes: pmid, title, section, publication_date, journal

### RAG Service
- Retrieval with optional cross-encoder reranking (ms-marco-MiniLM-L-12-v2)
- Hallucination check: Validates that cited PMIDs exist in retrieved sources
- Response caching in Redis (7-day TTL for RAG responses)

### Search & Recommendation
- Semantic search with query expansion (biomedical synonyms)
- Hybrid recommendation: 70% content similarity + 30% citation network

## API Endpoints Structure

```
/auth/*           - Authentication (JWT-based)
/search           - Semantic paper search
/chat/query       - RAG Q&A endpoint
/recommendations  - Similar papers, trending topics
/analytics        - Keyword trends, emerging topics
```

## Database Schema Highlights

Key PostgreSQL tables:
- `papers`: pmid (PK), title, abstract, full_text, doi, journal, publication_date
- `chunks`: id (UUID), paper_pmid (FK), section, text, chunk_index
- `users`: id (UUID), email, password_hash
- `query_logs`: For analytics and monitoring

Vector DB collection: `biomedical_papers` with cosine similarity

## Performance Targets

| Operation | p50 | p95 |
|-----------|-----|-----|
| Search | 200ms | 500ms |
| RAG Query | 1s | 2s |
| Recommendation | 100ms | 300ms |

## Development Guidelines

### RAG Response Format
All RAG responses must:
1. Cite sources with `[PMID: xxxxx]` format
2. Only use information from retrieved context
3. Acknowledge when context is insufficient

### Embedding Generation
```python
# Always use PubMedBERT for biomedical text
from transformers import AutoTokenizer, AutoModel
model_name = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"
```

### Chunking Standards
- Max chunk size: 512 tokens
- Overlap: 50 tokens
- Always preserve section boundaries when possible

### API Rate Limits
- Search: 60/minute
- RAG query: 20/minute (higher LLM cost)
- General API: 100/minute

## Environment Variables

Required:
- `PUBMED_API_KEY`: PubMed E-utilities API key
- `OPENAI_API_KEY`: OpenAI API key for GPT-4
- `JWT_SECRET_KEY`: JWT signing secret
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## Testing

Quality metrics to maintain:
- RAG retrieval: Precision@10, Recall@10, MRR
- Answer quality: LLM-as-a-Judge scoring (target: 4.0/5.0 average)
- Load testing: 500 concurrent users, 100 RPS baseline

## Build and Run Commands

### Backend (FastAPI)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Run Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Run Celery beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend (Next.js)
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check
```

### Docker (Full Stack)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

## Project Structure

```
Bio2/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── workers/         # Celery tasks
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Next.js pages
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API client
│   │   └── styles/          # CSS/Tailwind
│   └── package.json
└── docker-compose.yml
