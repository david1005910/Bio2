from typing import List, Optional, Dict
import numpy as np
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.paper import Paper, Citation
from app.services.embedding import EmbeddingGenerator, get_embedding_generator
from app.services.vector_store import VectorStore, get_vector_store


class PaperRecommender:
    """
    Paper recommendation system using content-based and citation-based methods.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_generator = embedding_generator or get_embedding_generator()

    async def recommend_similar_papers(
        self,
        pmid: str,
        top_k: int = 5,
        method: str = "hybrid",
        db: Optional[AsyncSession] = None
    ) -> List[dict]:
        """
        Get similar paper recommendations.

        Args:
            pmid: Source paper PMID
            top_k: Number of recommendations
            method: 'content', 'citation', or 'hybrid'
            db: Database session for citation data

        Returns:
            List of recommended papers with scores
        """
        if method == "content":
            return await self._content_based_recommendation(pmid, top_k)
        elif method == "citation" and db:
            return await self._citation_based_recommendation(pmid, top_k, db)
        elif method == "hybrid" and db:
            return await self._hybrid_recommendation(pmid, top_k, db)
        else:
            # Default to content-based
            return await self._content_based_recommendation(pmid, top_k)

    async def _content_based_recommendation(
        self,
        pmid: str,
        top_k: int
    ) -> List[dict]:
        """
        Content-based recommendation using embedding similarity.
        """
        # Get chunks for the paper
        paper_chunks = self.vector_store.search_by_pmid(pmid)

        if not paper_chunks:
            return []

        # Compute average embedding for the paper
        chunk_texts = [c["text"] for c in paper_chunks]
        embeddings = self.embedding_generator.batch_encode(chunk_texts)
        paper_embedding = np.mean(embeddings, axis=0)

        # Search for similar papers
        similar = self.vector_store.search(
            query_embedding=paper_embedding,
            top_k=top_k * 3  # Get more to deduplicate
        )

        # Aggregate by paper and exclude source
        paper_scores: Dict[str, dict] = {}

        for result in similar:
            result_pmid = result["metadata"].get("pmid", "")

            # Skip source paper
            if result_pmid == pmid or not result_pmid:
                continue

            if result_pmid not in paper_scores:
                paper_scores[result_pmid] = {
                    "pmid": result_pmid,
                    "title": result["metadata"].get("title", ""),
                    "similarity_score": result["similarity"],
                    "journal": result["metadata"].get("journal"),
                    "recommendation_type": "content"
                }
            else:
                # Update if better score
                if result["similarity"] > paper_scores[result_pmid]["similarity_score"]:
                    paper_scores[result_pmid]["similarity_score"] = result["similarity"]

        # Sort and return top-k
        sorted_papers = sorted(
            paper_scores.values(),
            key=lambda x: x["similarity_score"],
            reverse=True
        )

        return sorted_papers[:top_k]

    async def _citation_based_recommendation(
        self,
        pmid: str,
        top_k: int,
        db: AsyncSession
    ) -> List[dict]:
        """
        Citation-based recommendation using co-citation analysis.
        """
        # Get papers that cite this paper
        citing_result = await db.execute(
            select(Citation.citing_pmid).where(Citation.cited_pmid == pmid)
        )
        citing_pmids = [row[0] for row in citing_result.fetchall()]

        # Get papers cited by this paper
        cited_result = await db.execute(
            select(Citation.cited_pmid).where(Citation.citing_pmid == pmid)
        )
        cited_pmids = [row[0] for row in cited_result.fetchall()]

        # Co-citation analysis: find papers frequently cited alongside this one
        co_citation_scores: Dict[str, float] = defaultdict(float)

        # Papers that cite the same papers we cite
        for cited in cited_pmids:
            result = await db.execute(
                select(Citation.citing_pmid).where(Citation.cited_pmid == cited)
            )
            co_citers = [row[0] for row in result.fetchall()]
            for co_citer in co_citers:
                if co_citer != pmid:
                    co_citation_scores[co_citer] += 1.0

        # Papers cited by papers that cite us
        for citer in citing_pmids:
            result = await db.execute(
                select(Citation.cited_pmid).where(Citation.citing_pmid == citer)
            )
            co_cited = [row[0] for row in result.fetchall()]
            for paper in co_cited:
                if paper != pmid:
                    co_citation_scores[paper] += 0.5

        # Get paper details
        recommendations = []
        for rec_pmid, score in sorted(
            co_citation_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]:
            paper_result = await db.execute(
                select(Paper).where(Paper.pmid == rec_pmid)
            )
            paper = paper_result.scalar_one_or_none()

            if paper:
                recommendations.append({
                    "pmid": paper.pmid,
                    "title": paper.title,
                    "similarity_score": score / max(co_citation_scores.values()),
                    "journal": paper.journal,
                    "citation_count": paper.citation_count,
                    "recommendation_type": "citation"
                })

        return recommendations

    async def _hybrid_recommendation(
        self,
        pmid: str,
        top_k: int,
        db: AsyncSession,
        content_weight: float = 0.7
    ) -> List[dict]:
        """
        Hybrid recommendation combining content and citation methods.
        """
        # Get both types of recommendations
        content_recs = await self._content_based_recommendation(pmid, top_k * 2)
        citation_recs = await self._citation_based_recommendation(pmid, top_k * 2, db)

        # Normalize and combine scores
        content_scores = {
            r["pmid"]: r["similarity_score"]
            for r in content_recs
        }
        citation_scores = {
            r["pmid"]: r["similarity_score"]
            for r in citation_recs
        }

        # Normalize
        if content_scores:
            max_content = max(content_scores.values())
            content_scores = {k: v / max_content for k, v in content_scores.items()}

        if citation_scores:
            max_citation = max(citation_scores.values())
            citation_scores = {k: v / max_citation for k, v in citation_scores.items()}

        # Combine
        all_pmids = set(content_scores.keys()) | set(citation_scores.keys())
        hybrid_scores: Dict[str, float] = {}

        for rec_pmid in all_pmids:
            content_score = content_scores.get(rec_pmid, 0)
            citation_score = citation_scores.get(rec_pmid, 0)
            hybrid_scores[rec_pmid] = (
                content_weight * content_score +
                (1 - content_weight) * citation_score
            )

        # Build recommendations list
        paper_info = {r["pmid"]: r for r in content_recs + citation_recs}

        recommendations = []
        for rec_pmid, score in sorted(
            hybrid_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]:
            info = paper_info.get(rec_pmid, {"pmid": rec_pmid})
            recommendations.append({
                "pmid": rec_pmid,
                "title": info.get("title", ""),
                "similarity_score": score,
                "journal": info.get("journal"),
                "citation_count": info.get("citation_count", 0),
                "recommendation_type": "hybrid"
            })

        return recommendations

    async def get_trending_papers(
        self,
        days: int = 30,
        top_k: int = 10,
        db: AsyncSession = None
    ) -> List[dict]:
        """
        Get trending papers based on recent activity.
        """
        from datetime import datetime, timedelta

        if not db:
            return []

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(Paper)
            .where(Paper.publication_date >= cutoff_date)
            .order_by(Paper.citation_count.desc())
            .limit(top_k)
        )
        papers = result.scalars().all()

        return [
            {
                "pmid": p.pmid,
                "title": p.title,
                "journal": p.journal,
                "citation_count": p.citation_count,
                "publication_date": p.publication_date
            }
            for p in papers
        ]


def get_recommender() -> PaperRecommender:
    """Get recommender instance"""
    return PaperRecommender()
