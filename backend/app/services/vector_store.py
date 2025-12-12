from typing import List, Optional, Dict, Any
import numpy as np
from uuid import uuid4
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings


class VectorStore:
    """
    ChromaDB-based vector store for biomedical paper embeddings.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_directory: Optional[str] = None):
        if self._initialized:
            return

        persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR

        # Use PersistentClient for data persistence across restarts
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="biomedical_papers",
            metadata={"hnsw:space": "cosine"}
        )

        self._initialized = True

    def add_chunks(
        self,
        chunks: List[dict],
        embeddings: np.ndarray
    ) -> List[str]:
        """
        Add chunks with embeddings to vector store.

        Args:
            chunks: List of chunk dicts with pmid, title, section, text, etc.
            embeddings: numpy array of embeddings, shape (n_chunks, dim)

        Returns:
            List of generated chunk IDs
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        ids = [str(uuid4()) for _ in chunks]

        documents = [chunk["text"] for chunk in chunks]

        metadatas = []
        for chunk in chunks:
            metadata = {
                "pmid": chunk["pmid"],
                "title": chunk["title"],
                "section": chunk.get("section", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "token_count": chunk.get("token_count", 0),
            }
            # Add optional metadata
            for key in ["journal", "publication_date", "authors"]:
                if key in chunk:
                    metadata[key] = str(chunk[key])

            metadatas.append(metadata)

        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas
        )

        return ids

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_dict: Optional[dict] = None
    ) -> List[dict]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector, shape (dim,)
            top_k: Number of results to return
            filter_dict: Metadata filter (e.g., {'section': 'abstract'})

        Returns:
            List of result dicts with id, text, distance, metadata
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=filter_dict
        )

        formatted_results = []

        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                result = {
                    "id": chunk_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                }
                # Convert distance to similarity score (for cosine, distance is 1 - similarity)
                result["similarity"] = 1 - result["distance"]
                formatted_results.append(result)

        return formatted_results

    def search_by_pmid(
        self,
        pmid: str,
        top_k: int = 10
    ) -> List[dict]:
        """Get all chunks for a specific paper"""
        results = self.collection.get(
            where={"pmid": pmid},
            limit=top_k
        )

        formatted_results = []
        if results["ids"]:
            for i, chunk_id in enumerate(results["ids"]):
                formatted_results.append({
                    "id": chunk_id,
                    "text": results["documents"][i] if results["documents"] else "",
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })

        return formatted_results

    def delete_by_pmid(self, pmid: str) -> int:
        """
        Delete all chunks for a paper.

        Returns:
            Number of chunks deleted
        """
        # Get chunk IDs first
        results = self.collection.get(
            where={"pmid": pmid}
        )

        if not results["ids"]:
            return 0

        self.collection.delete(ids=results["ids"])
        return len(results["ids"])

    def delete_by_ids(self, ids: List[str]) -> None:
        """Delete chunks by their IDs"""
        self.collection.delete(ids=ids)

    def update_metadata(
        self,
        chunk_id: str,
        metadata: dict
    ) -> None:
        """Update metadata for a chunk"""
        self.collection.update(
            ids=[chunk_id],
            metadatas=[metadata]
        )

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection"""
        count = self.collection.count()

        # Get sample of PMIDs
        sample = self.collection.peek(limit=100)
        unique_pmids = set()
        if sample["metadatas"]:
            for metadata in sample["metadatas"]:
                if "pmid" in metadata:
                    unique_pmids.add(metadata["pmid"])

        return {
            "total_chunks": count,
            "sample_unique_papers": len(unique_pmids),
            "collection_name": "biomedical_papers"
        }

    def similarity_search_with_score(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.5
    ) -> List[dict]:
        """
        Search with minimum similarity threshold.

        Args:
            query_embedding: Query vector
            top_k: Max results
            score_threshold: Minimum similarity score (0-1)

        Returns:
            Filtered results above threshold
        """
        results = self.search(query_embedding, top_k=top_k * 2)

        filtered = [
            r for r in results
            if r["similarity"] >= score_threshold
        ]

        return filtered[:top_k]


class FAISSVectorStore:
    """
    FAISS-based vector store for large-scale search.
    Use when ChromaDB becomes too slow.
    """

    def __init__(self, dimension: int = 768):
        import faiss

        self.dimension = dimension

        # IndexFlatIP for cosine similarity (after L2 normalization)
        self.index = faiss.IndexFlatIP(dimension)

        # ID mapping: faiss_idx -> chunk_id
        self.id_map: Dict[int, str] = {}
        # Reverse mapping
        self.reverse_id_map: Dict[str, int] = {}
        # Metadata storage
        self.metadata_store: Dict[str, dict] = {}
        # Document storage
        self.document_store: Dict[str, str] = {}

    def add_vectors(
        self,
        embeddings: np.ndarray,
        chunk_ids: List[str],
        metadatas: Optional[List[dict]] = None,
        documents: Optional[List[str]] = None
    ) -> None:
        """Add vectors to the index"""
        import faiss

        if len(embeddings) != len(chunk_ids):
            raise ValueError("Number of embeddings must match chunk IDs")

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings.astype(np.float32))

        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings.astype(np.float32))

        # Update mappings
        for i, chunk_id in enumerate(chunk_ids):
            faiss_idx = start_idx + i
            self.id_map[faiss_idx] = chunk_id
            self.reverse_id_map[chunk_id] = faiss_idx

            if metadatas and i < len(metadatas):
                self.metadata_store[chunk_id] = metadatas[i]

            if documents and i < len(documents):
                self.document_store[chunk_id] = documents[i]

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[dict]:
        """Search for similar vectors"""
        import faiss

        # Reshape and normalize
        query = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query)

        # Search
        distances, indices = self.index.search(query, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < 0:  # FAISS returns -1 for empty results
                continue

            chunk_id = self.id_map.get(idx, "")
            results.append({
                "id": chunk_id,
                "text": self.document_store.get(chunk_id, ""),
                "similarity": float(dist),  # Already cosine similarity due to IP
                "metadata": self.metadata_store.get(chunk_id, {})
            })

        return results

    def save_index(self, path: str) -> None:
        """Save FAISS index to file"""
        import faiss
        faiss.write_index(self.index, path)

    def load_index(self, path: str) -> None:
        """Load FAISS index from file"""
        import faiss
        self.index = faiss.read_index(path)

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance"""
    return VectorStore()
