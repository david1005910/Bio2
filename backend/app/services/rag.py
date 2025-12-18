import re
import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.services.embedding import EmbeddingGenerator, get_embedding_generator
from app.services.vector_store import VectorStore, get_vector_store


@dataclass
class RAGResponse:
    answer: str
    sources: List[dict]
    confidence: float
    chunks_used: List[dict]


@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float
    cited_sources: List[str]
    warnings: List[str]


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) service for biomedical Q&A.
    """

    SYSTEM_PROMPT = """You are an expert biomedical researcher assistant. Answer the question based on the provided research paper excerpts.

IMPORTANT RULES:
1. Only use information from the provided context
2. Cite sources using [PMID: xxxxx] format
3. If the context doesn't contain enough information, say "I cannot find sufficient information in the provided papers"
4. Do not make assumptions or add information not present in the context
5. Be precise and factual
6. Explain complex terms when needed"""

    PROMPT_TEMPLATE = """Context from research papers:
{context}

Question: {question}

Provide a detailed answer with citations:"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        self.vector_store = vector_store or get_vector_store()
        self.embedding_generator = embedding_generator or get_embedding_generator()

        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL

        # Initialize reranker (lazy load)
        self._reranker = None

    @property
    def reranker(self):
        """Lazy load reranker model"""
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(settings.RERANK_MODEL)
        return self._reranker

    async def query(
        self,
        question: str,
        top_k: int = 5,
        rerank: bool = True,
        temperature: float = None,
        filter_dict: Optional[dict] = None
    ) -> RAGResponse:
        """
        Answer a question using RAG.

        Workflow:
        1. Embed question
        2. Vector search
        3. Re-rank (optional)
        4. Build context
        5. Generate answer
        6. Validate response

        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            rerank: Whether to rerank results
            temperature: LLM temperature
            filter_dict: Metadata filter

        Returns:
            RAGResponse with answer, sources, confidence
        """
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

        # 1. Embed question
        question_embedding = self.embedding_generator.encode(question)

        # 2. Vector search (retrieve more for reranking)
        search_k = top_k * 2 if rerank else top_k
        search_results = self.vector_store.search(
            query_embedding=question_embedding,
            top_k=search_k,
            filter_dict=filter_dict
        )

        if not search_results:
            return RAGResponse(
                answer="I could not find any relevant information in the database to answer your question.",
                sources=[],
                confidence=0.0,
                chunks_used=[]
            )

        # 3. Re-rank results
        if rerank and len(search_results) > top_k:
            search_results = self._rerank_results(question, search_results)[:top_k]

        # 4. Build context
        context = self._build_context(search_results)

        # 5. Generate answer
        answer = await self._generate_answer(question, context, temp)

        # 6. Validate response
        validation = self._validate_response(answer, search_results)

        # Extract source info
        sources = self._extract_sources(search_results)

        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=validation.confidence,
            chunks_used=search_results
        )

    def _build_context(self, search_results: List[dict]) -> str:
        """Build context string from search results"""
        context_parts = []

        for i, result in enumerate(search_results, 1):
            pmid = result["metadata"].get("pmid", "unknown")
            title = result["metadata"].get("title", "")
            section = result["metadata"].get("section", "")
            text = result["text"]

            context_parts.append(
                f"[Paper {i}] PMID: {pmid}\n"
                f"Title: {title}\n"
                f"Section: {section}\n"
                f"Content: {text}\n"
            )

        return "\n\n".join(context_parts)

    def _rerank_results(
        self,
        question: str,
        results: List[dict]
    ) -> List[dict]:
        """Re-rank results using cross-encoder"""
        # Create (question, passage) pairs
        pairs = [(question, r["text"]) for r in results]

        # Score pairs
        scores = self.reranker.predict(pairs)

        # Sort by score
        ranked = sorted(
            zip(scores, results),
            key=lambda x: x[0],
            reverse=True
        )

        return [result for _, result in ranked]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_answer(
        self,
        question: str,
        context: str,
        temperature: float
    ) -> str:
        """Generate answer using LLM"""
        prompt = self.PROMPT_TEMPLATE.format(
            context=context,
            question=question
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=settings.LLM_MAX_TOKENS
        )

        return response.choices[0].message.content

    def _validate_response(
        self,
        answer: str,
        sources: List[dict]
    ) -> ValidationResult:
        """
        Validate response for hallucination.

        Checks:
        1. Cited PMIDs exist in sources
        2. Response acknowledges uncertainty when appropriate
        """
        warnings = []

        # Extract cited PMIDs from answer
        cited_pmids = re.findall(r"PMID:\s*(\d+)", answer)

        # Get source PMIDs
        source_pmids = [
            s["metadata"].get("pmid", "")
            for s in sources
        ]

        # Check citation validity
        invalid_citations = [
            pmid for pmid in cited_pmids
            if pmid not in source_pmids
        ]

        if invalid_citations:
            warnings.append(f"Invalid citations: {invalid_citations}")

        # Calculate confidence
        if not cited_pmids:
            # No citations might indicate uncertainty or generic response
            confidence = 0.5
            warnings.append("No citations in response")
        elif invalid_citations:
            confidence = 0.3
        else:
            # All citations valid
            confidence = 0.9

        return ValidationResult(
            is_valid=len(invalid_citations) == 0,
            confidence=confidence,
            cited_sources=cited_pmids,
            warnings=warnings
        )

    def _extract_sources(self, search_results: List[dict]) -> List[dict]:
        """Extract source information for response"""
        sources = []

        for result in search_results:
            metadata = result["metadata"]
            sources.append({
                "pmid": metadata.get("pmid", ""),
                "title": metadata.get("title", ""),
                "relevance": result.get("similarity", 0.0),
                "excerpt": result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"],
                "section": metadata.get("section", "")
            })

        return sources

    async def stream_response(
        self,
        question: str,
        top_k: int = 5
    ):
        """
        Stream response for real-time chat.
        Yields chunks of the answer as they're generated.
        """
        # Get context
        question_embedding = self.embedding_generator.encode(question)
        search_results = self.vector_store.search(
            query_embedding=question_embedding,
            top_k=top_k
        )

        context = self._build_context(search_results)
        prompt = self.PROMPT_TEMPLATE.format(
            context=context,
            question=question
        )

        # Stream response
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class ConversationManager:
    """Manage multi-turn conversations"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: dict = {}  # session_id -> messages

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None
    ) -> None:
        """Add message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        message = {
            "role": role,
            "content": content,
            "sources": sources
        }

        self.conversations[session_id].append(message)

        # Trim history if needed
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

    def get_history(self, session_id: str) -> List[dict]:
        """Get conversation history"""
        return self.conversations.get(session_id, [])

    def clear_history(self, session_id: str) -> None:
        """Clear conversation history"""
        if session_id in self.conversations:
            del self.conversations[session_id]

    def get_context_messages(self, session_id: str) -> List[dict]:
        """Get messages formatted for LLM context"""
        history = self.get_history(session_id)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]


def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()
