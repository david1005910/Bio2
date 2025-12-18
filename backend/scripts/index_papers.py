#!/usr/bin/env python3
"""
Index papers from database into vector store with PubMedBERT embeddings.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import async_session_maker
from app.models.paper import Paper
from app.services.embedding import get_embedding_generator, get_text_chunker
from app.services.vector_store import get_vector_store
from sqlalchemy import select


async def index_papers():
    """Index all papers from database into vector store"""

    print("Loading embedding model (PubMedBERT)...")
    embedding_generator = get_embedding_generator()
    chunker = get_text_chunker()
    vector_store = get_vector_store()

    print(f"Model loaded: {embedding_generator.model_name}")
    print(f"Embedding dimension: {embedding_generator.dimension}")

    # Get current vector store stats
    stats = vector_store.get_collection_stats()
    print(f"Current vector store: {stats['total_chunks']} chunks")

    # Get papers from database
    async with async_session_maker() as session:
        result = await session.execute(select(Paper))
        papers = result.scalars().all()

    print(f"\nFound {len(papers)} papers in database")

    if not papers:
        print("No papers to index!")
        return

    # Process each paper
    total_chunks = 0
    for i, paper in enumerate(papers, 1):
        print(f"\n[{i}/{len(papers)}] Processing: {paper.pmid} - {paper.title[:50]}...")

        # Check if already indexed
        existing = vector_store.search_by_pmid(paper.pmid)
        if existing:
            print(f"  Already indexed ({len(existing)} chunks), skipping")
            continue

        # Create chunks
        chunks = chunker.chunk_paper(
            pmid=paper.pmid,
            title=paper.title,
            abstract=paper.abstract or "",
            full_text=paper.full_text
        )

        if not chunks:
            print(f"  No chunks created, skipping")
            continue

        # Add metadata
        for chunk in chunks:
            chunk["journal"] = paper.journal or ""
            chunk["publication_date"] = str(paper.publication_date) if paper.publication_date else ""

        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        print(f"  Generating embeddings for {len(chunks)} chunks...")
        embeddings = embedding_generator.batch_encode(texts)

        # Add to vector store
        chunk_ids = vector_store.add_chunks(chunks, embeddings)
        total_chunks += len(chunk_ids)
        print(f"  Added {len(chunk_ids)} chunks to vector store")

    # Final stats
    final_stats = vector_store.get_collection_stats()
    print(f"\n{'='*60}")
    print(f"Indexing complete!")
    print(f"Total chunks in vector store: {final_stats['total_chunks']}")
    print(f"New chunks added: {total_chunks}")


async def test_search(query: str):
    """Test semantic search"""
    print(f"\n{'='*60}")
    print(f"Testing search: '{query}'")
    print(f"{'='*60}")

    embedding_generator = get_embedding_generator()
    vector_store = get_vector_store()

    # Generate query embedding
    query_embedding = embedding_generator.encode(query)

    # Search
    results = vector_store.search(query_embedding, top_k=5)

    print(f"\nTop {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [PMID: {result['metadata'].get('pmid', 'N/A')}] "
              f"(similarity: {result['similarity']:.3f})")
        print(f"   Section: {result['metadata'].get('section', 'N/A')}")
        print(f"   Title: {result['metadata'].get('title', 'N/A')[:60]}...")
        print(f"   Text: {result['text'][:200]}...")


async def main():
    # Index papers
    await index_papers()

    # Test searches
    test_queries = [
        "cancer immunotherapy treatment",
        "CRISPR gene editing applications",
        "COVID-19 vaccine efficacy",
    ]

    for query in test_queries:
        await test_search(query)


if __name__ == "__main__":
    asyncio.run(main())
