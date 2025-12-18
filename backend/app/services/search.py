from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.config import settings
from app.models.paper import Paper, Keyword, PaperKeyword
from app.services.embedding import EmbeddingGenerator, get_embedding_generator
from app.services.vector_store import VectorStore, get_vector_store
from app.schemas.search import SearchFilters, SearchResult


class SemanticSearchService:
    """
    Semantic search service combining vector similarity and metadata filtering.
    """

    # Biomedical synonym expansions
    SYNONYMS = {
        "t cell": ["t lymphocyte", "t-cell"],
        "cancer": ["carcinoma", "tumor", "malignancy", "neoplasm"],
        "crispr": ["crispr-cas9", "crispr/cas9", "gene editing"],
        "car-t": ["car t", "chimeric antigen receptor"],
        "immunotherapy": ["immune therapy", "immunotherapeutic"],
        "antibody": ["immunoglobulin", "mab", "monoclonal antibody"],
        "rna": ["ribonucleic acid"],
        "dna": ["deoxyribonucleic acid"],
        "gene": ["genetic", "genomic"],
        "protein": ["proteomic", "polypeptide"],
    }

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_generator = embedding_generator or get_embedding_generator()

        # Lazy load reranker
        self._reranker = None

    @property
    def reranker(self):
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(settings.RERANK_MODEL)
        return self._reranker

    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = 10,
        rerank: bool = True,
        db: Optional[AsyncSession] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search for papers.

        Args:
            query: Natural language search query
            filters: Search filters (year, journal, etc.)
            top_k: Number of results
            rerank: Whether to rerank results
            db: Database session for metadata enrichment

        Returns:
            List of SearchResult objects
        """
        # 1. Expand query with synonyms
        expanded_query = self._expand_query(query)

        # 2. Embed query
        query_embedding = self.embedding_generator.encode(expanded_query)

        # 3. Vector search
        vector_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 3  # Get more for filtering and deduplication
        )

        if not vector_results:
            return []

        # 4. Aggregate by paper (group chunks)
        paper_results = self._aggregate_by_paper(vector_results)

        # 5. Apply metadata filters
        if filters:
            paper_results = self._apply_filters(paper_results, filters)

        # 6. Rerank if requested
        if rerank and len(paper_results) > 1:
            paper_results = self._rerank_papers(query, paper_results)

        # 7. Format results
        results = []
        for paper_data in paper_results[:top_k]:
            results.append(SearchResult(
                pmid=paper_data["pmid"],
                title=paper_data["title"],
                abstract=paper_data.get("abstract"),
                relevance_score=paper_data["score"],
                publication_date=paper_data.get("publication_date"),
                journal=paper_data.get("journal"),
                authors=paper_data.get("authors", []),
                citation_count=paper_data.get("citation_count", 0),
                keywords=paper_data.get("keywords", []),
                matched_chunks=paper_data.get("matched_chunks", [])
            ))

        return results

    def _expand_query(self, query: str) -> str:
        """
        Expand query with synonyms for better recall.

        Example: "T cell" → "T cell T lymphocyte t-cell"
        """
        expanded_terms = [query]

        query_lower = query.lower()
        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                expanded_terms.extend(synonyms)

        return " ".join(expanded_terms)

    def _aggregate_by_paper(self, chunk_results: List[dict]) -> List[dict]:
        """
        Aggregate chunk results by paper PMID.

        Takes the best chunk score for each paper.
        """
        paper_scores: Dict[str, dict] = {}

        for result in chunk_results:
            pmid = result["metadata"].get("pmid", "")
            if not pmid:
                continue

            if pmid not in paper_scores:
                paper_scores[pmid] = {
                    "pmid": pmid,
                    "title": result["metadata"].get("title", ""),
                    "journal": result["metadata"].get("journal"),
                    "score": result["similarity"],
                    "chunks": [result],
                    "matched_chunks": [result["text"][:200]]
                }
            else:
                # Update if this chunk has higher score
                if result["similarity"] > paper_scores[pmid]["score"]:
                    paper_scores[pmid]["score"] = result["similarity"]

                paper_scores[pmid]["chunks"].append(result)
                if len(paper_scores[pmid]["matched_chunks"]) < 3:
                    paper_scores[pmid]["matched_chunks"].append(result["text"][:200])

        # Sort by score
        return sorted(
            paper_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

    def _apply_filters(
        self,
        papers: List[dict],
        filters: SearchFilters
    ) -> List[dict]:
        """Apply metadata filters to papers"""
        filtered = papers

        # Year filter
        if filters.year_start or filters.year_end:
            def year_match(paper):
                pub_date = paper.get("publication_date")
                if not pub_date:
                    return True  # Include papers without date

                if isinstance(pub_date, str):
                    try:
                        year = int(pub_date[:4])
                    except (ValueError, IndexError):
                        return True
                elif hasattr(pub_date, "year"):
                    year = pub_date.year
                else:
                    return True

                if filters.year_start and year < filters.year_start:
                    return False
                if filters.year_end and year > filters.year_end:
                    return False
                return True

            filtered = [p for p in filtered if year_match(p)]

        # Journal filter
        if filters.journals:
            journals_lower = [j.lower() for j in filters.journals]
            filtered = [
                p for p in filtered
                if not p.get("journal") or
                any(j in p.get("journal", "").lower() for j in journals_lower)
            ]

        # Sort by specified criteria
        if filters.sort_by == "date":
            filtered = sorted(
                filtered,
                key=lambda x: x.get("publication_date") or "",
                reverse=True
            )
        elif filters.sort_by == "citations":
            filtered = sorted(
                filtered,
                key=lambda x: x.get("citation_count", 0),
                reverse=True
            )
        # 'relevance' keeps existing order (by score)

        return filtered

    def _rerank_papers(
        self,
        query: str,
        papers: List[dict]
    ) -> List[dict]:
        """Rerank papers using cross-encoder"""
        # Use best chunk from each paper for reranking
        pairs = []
        for paper in papers:
            # Combine title and best chunk
            best_chunk = paper["chunks"][0]["text"] if paper.get("chunks") else ""
            text = f"{paper['title']} {best_chunk}"
            pairs.append((query, text))

        # Score
        scores = self.reranker.predict(pairs)

        # Sort by rerank score
        reranked = sorted(
            zip(scores, papers),
            key=lambda x: x[0],
            reverse=True
        )

        # Update scores
        for new_score, paper in reranked:
            paper["score"] = float(new_score)

        return [paper for _, paper in reranked]

    async def get_paper_details(
        self,
        pmid: str,
        db: AsyncSession
    ) -> Optional[dict]:
        """Get detailed paper information from database"""
        result = await db.execute(
            select(Paper).where(Paper.pmid == pmid)
        )
        paper = result.scalar_one_or_none()

        if not paper:
            return None

        # Get authors
        authors = []
        for pa in paper.authors:
            authors.append(pa.author.name)

        # Get keywords
        keywords = []
        for pk in paper.keywords:
            keywords.append(pk.keyword.term)

        return {
            "pmid": paper.pmid,
            "title": paper.title,
            "abstract": paper.abstract,
            "journal": paper.journal,
            "publication_date": paper.publication_date,
            "doi": paper.doi,
            "citation_count": paper.citation_count,
            "authors": authors,
            "keywords": keywords
        }


def get_search_service() -> SemanticSearchService:
    """Get search service instance"""
    return SemanticSearchService()
