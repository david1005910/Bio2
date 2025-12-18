import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.core.config import settings
from app.services.pubmed import PubMedCollector, PaperMetadata
from app.services.embedding import EmbeddingGenerator, TextChunker
from app.services.vector_store import VectorStore


def run_async(coro):
    """Helper to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def daily_paper_crawl(self, keywords: Optional[List[str]] = None):
    """
    Daily task to crawl new papers from PubMed.

    Args:
        keywords: List of keywords to search. Defaults to biomedical topics.
    """
    if keywords is None:
        keywords = [
            "cancer immunotherapy",
            "CRISPR",
            "CAR-T cell therapy",
            "gene therapy",
            "mRNA vaccine",
            "single cell sequencing",
            "protein structure prediction",
            "drug discovery AI",
        ]

    collector = PubMedCollector()

    # Date range: yesterday to today
    end_date = datetime.utcnow().strftime("%Y/%m/%d")
    start_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y/%m/%d")

    total_papers = 0
    errors = []

    for keyword in keywords:
        try:
            # Search for papers
            pmids = run_async(
                collector.search_papers(
                    query=f"{keyword}[Title/Abstract]",
                    max_results=100,
                    date_range=(start_date, end_date)
                )
            )

            if not pmids:
                continue

            # Fetch paper details
            papers = run_async(collector.batch_fetch(pmids))

            # Queue processing for each paper
            for paper in papers:
                process_paper.delay(paper.__dict__)

            total_papers += len(papers)

        except Exception as e:
            errors.append(f"{keyword}: {str(e)}")

    return {
        "status": "completed",
        "total_papers_found": total_papers,
        "keywords_searched": len(keywords),
        "errors": errors
    }


@celery_app.task(bind=True, max_retries=3)
def process_paper(self, paper_data: dict):
    """
    Process a single paper: save to DB and generate embeddings.

    Args:
        paper_data: Dictionary with paper metadata
    """
    from app.core.database import async_session_maker
    from app.models.paper import Paper, Author, PaperAuthor, Keyword, PaperKeyword, Chunk

    async def _process():
        async with async_session_maker() as db:
            # Check if paper exists
            result = await db.execute(
                select(Paper).where(Paper.pmid == paper_data["pmid"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                return {"status": "skipped", "reason": "already exists"}

            # Create paper
            paper = Paper(
                pmid=paper_data["pmid"],
                title=paper_data["title"],
                abstract=paper_data["abstract"],
                journal=paper_data["journal"],
                publication_date=paper_data.get("publication_date"),
                doi=paper_data.get("doi"),
            )
            db.add(paper)

            # Add authors
            for i, author_name in enumerate(paper_data.get("authors", [])):
                # Check if author exists
                author_result = await db.execute(
                    select(Author).where(Author.name == author_name)
                )
                author = author_result.scalar_one_or_none()

                if not author:
                    author = Author(name=author_name)
                    db.add(author)
                    await db.flush()

                paper_author = PaperAuthor(
                    paper_pmid=paper_data["pmid"],
                    author_id=author.id,
                    author_order=i + 1
                )
                db.add(paper_author)

            # Add keywords (including MeSH terms)
            all_keywords = paper_data.get("keywords", []) + paper_data.get("mesh_terms", [])
            for term in all_keywords:
                keyword_result = await db.execute(
                    select(Keyword).where(Keyword.term == term)
                )
                keyword = keyword_result.scalar_one_or_none()

                if not keyword:
                    keyword = Keyword(
                        term=term,
                        type="mesh" if term in paper_data.get("mesh_terms", []) else "author"
                    )
                    db.add(keyword)
                    await db.flush()

                paper_keyword = PaperKeyword(
                    paper_pmid=paper_data["pmid"],
                    keyword_id=keyword.id
                )
                db.add(paper_keyword)

            await db.commit()

        return {"status": "success", "pmid": paper_data["pmid"]}

    result = run_async(_process())

    # Queue embedding generation
    if result["status"] == "success":
        generate_embeddings.delay(paper_data["pmid"])

    return result


@celery_app.task(bind=True, max_retries=3)
def generate_embeddings(self, pmid: str):
    """
    Generate embeddings for a paper and store in vector DB.

    Args:
        pmid: Paper PMID
    """
    from app.core.database import async_session_maker
    from app.models.paper import Paper, Chunk

    async def _generate():
        async with async_session_maker() as db:
            # Get paper
            result = await db.execute(
                select(Paper).where(Paper.pmid == pmid)
            )
            paper = result.scalar_one_or_none()

            if not paper:
                return {"status": "error", "reason": "paper not found"}

            # Create chunks
            chunker = TextChunker()
            chunks = chunker.chunk_paper(
                pmid=paper.pmid,
                title=paper.title,
                abstract=paper.abstract or "",
                full_text=paper.full_text
            )

            if not chunks:
                return {"status": "skipped", "reason": "no content to embed"}

            # Generate embeddings
            embedding_gen = EmbeddingGenerator()
            texts = [c["text"] for c in chunks]
            embeddings = embedding_gen.batch_encode(texts)

            # Store in vector DB
            vector_store = VectorStore()
            chunk_ids = vector_store.add_chunks(chunks, embeddings)

            # Store chunk references in DB
            for i, chunk_data in enumerate(chunks):
                chunk = Chunk(
                    id=chunk_ids[i] if i < len(chunk_ids) else None,
                    paper_pmid=pmid,
                    section=chunk_data.get("section"),
                    text=chunk_data["text"],
                    chunk_index=chunk_data.get("chunk_index", i),
                    token_count=chunk_data.get("token_count")
                )
                db.add(chunk)

            await db.commit()

        return {
            "status": "success",
            "pmid": pmid,
            "chunks_created": len(chunks)
        }

    return run_async(_generate())


@celery_app.task(bind=True)
def refresh_embeddings(self, batch_size: int = 100):
    """
    Refresh embeddings for papers that haven't been processed.
    """
    from app.core.database import async_session_maker
    from app.models.paper import Paper, Chunk

    async def _refresh():
        async with async_session_maker() as db:
            # Find papers without chunks
            result = await db.execute(
                select(Paper.pmid)
                .outerjoin(Chunk, Paper.pmid == Chunk.paper_pmid)
                .where(Chunk.id.is_(None))
                .limit(batch_size)
            )
            pmids = [row[0] for row in result.fetchall()]

        # Queue embedding generation
        for pmid in pmids:
            generate_embeddings.delay(pmid)

        return {
            "status": "completed",
            "papers_queued": len(pmids)
        }

    return run_async(_refresh())


@celery_app.task(bind=True)
def delete_paper_data(self, pmid: str):
    """
    Delete all data for a paper (DB records and vectors).
    """
    from app.core.database import async_session_maker
    from app.models.paper import Paper

    async def _delete():
        # Delete from vector store
        vector_store = VectorStore()
        deleted_chunks = vector_store.delete_by_pmid(pmid)

        # Delete from database
        async with async_session_maker() as db:
            result = await db.execute(
                select(Paper).where(Paper.pmid == pmid)
            )
            paper = result.scalar_one_or_none()

            if paper:
                await db.delete(paper)
                await db.commit()

        return {
            "status": "success",
            "pmid": pmid,
            "chunks_deleted": deleted_chunks
        }

    return run_async(_delete())
