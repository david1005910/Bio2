#!/usr/bin/env python3
"""
Test script to collect sample papers from PubMed and store in database.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pubmed import PubMedCollector
from app.core.database import async_session_maker
from app.models.paper import Paper
from sqlalchemy import select


async def collect_papers(query: str, max_results: int = 10):
    """Collect papers from PubMed and store in database"""
    collector = PubMedCollector()

    print(f"Searching PubMed for: {query}")
    pmids = await collector.search_papers(query, max_results=max_results)
    print(f"Found {len(pmids)} papers")

    if not pmids:
        print("No papers found!")
        return

    print("Fetching paper details...")
    papers = await collector.batch_fetch(pmids)
    print(f"Retrieved {len(papers)} paper details")

    # Store in database
    async with async_session_maker() as session:
        stored_count = 0

        for paper_data in papers:
            # Check if paper already exists
            existing = await session.execute(
                select(Paper).where(Paper.pmid == paper_data.pmid)
            )
            if existing.scalar_one_or_none():
                print(f"Paper {paper_data.pmid} already exists, skipping")
                continue

            # Create paper with authors stored as JSON-like string
            paper = Paper(
                pmid=paper_data.pmid,
                title=paper_data.title,
                abstract=paper_data.abstract,
                journal=paper_data.journal,
                publication_date=paper_data.publication_date,
                doi=paper_data.doi,
            )
            session.add(paper)
            stored_count += 1
            print(f"Stored: {paper_data.pmid} - {paper_data.title[:60]}...")

        await session.commit()
        print(f"\nSuccessfully stored {stored_count} new papers!")


async def main():
    # Sample biomedical queries
    queries = [
        "cancer immunotherapy[Title/Abstract]",
        "CRISPR gene editing[Title/Abstract]",
        "COVID-19 vaccine[Title/Abstract]",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        await collect_papers(query, max_results=5)
        print(f"{'='*60}")

    # Count total papers
    async with async_session_maker() as session:
        result = await session.execute(select(Paper))
        papers = result.scalars().all()
        print(f"\nTotal papers in database: {len(papers)}")


if __name__ == "__main__":
    asyncio.run(main())
