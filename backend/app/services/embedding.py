from typing import List, Optional
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from functools import lru_cache

from app.core.config import settings


class EmbeddingGenerator:
    """
    Generate embeddings using PubMedBERT or similar biomedical models.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to avoid loading model multiple times"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        if self._initialized:
            return

        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.eval()

        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self._initialized = True

    def encode(
        self,
        text: str,
        max_length: int = 512,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Convert text to embedding vector.

        Args:
            text: Input text
            max_length: Maximum token length
            normalize: Whether to L2 normalize the embedding

        Returns:
            numpy array of shape (768,)
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            max_length=max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        ).to(self.device)

        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embedding (first token)
            embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        embedding = embedding.squeeze()

        if normalize:
            embedding = embedding / np.linalg.norm(embedding)

        return embedding

    def batch_encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        max_length: int = 512,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Batch encode multiple texts.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            max_length: Maximum token length
            normalize: Whether to L2 normalize embeddings

        Returns:
            numpy array of shape (n_texts, 768)
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]

            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts,
                max_length=max_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt"
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            if normalize:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / norms

            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    def get_token_count(self, text: str) -> int:
        """Get token count for text"""
        tokens = self.tokenizer.tokenize(text)
        return len(tokens)


class TextChunker:
    """
    Split text into chunks for embedding and retrieval.
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        tokenizer: Optional[AutoTokenizer] = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        if tokenizer:
            self.tokenizer = tokenizer
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(settings.EMBEDDING_MODEL)

    def chunk_by_tokens(self, text: str) -> List[dict]:
        """
        Split text into fixed-size token chunks with overlap.

        Returns:
            List of dicts with 'text', 'start_idx', 'end_idx', 'token_count'
        """
        tokens = self.tokenizer.tokenize(text)
        chunks = []

        step_size = self.chunk_size - self.chunk_overlap

        for i in range(0, len(tokens), step_size):
            chunk_tokens = tokens[i:i + self.chunk_size]

            if len(chunk_tokens) < 50:  # Skip very short chunks
                continue

            chunk_text = self.tokenizer.convert_tokens_to_string(chunk_tokens)

            chunks.append({
                "text": chunk_text,
                "start_idx": i,
                "end_idx": min(i + self.chunk_size, len(tokens)),
                "token_count": len(chunk_tokens)
            })

        return chunks

    def chunk_by_section(
        self,
        sections: dict,
        pmid: str,
        title: str
    ) -> List[dict]:
        """
        Chunk paper by sections, sub-chunking if sections are too long.

        Args:
            sections: Dict mapping section names to text
            pmid: Paper PMID
            title: Paper title

        Returns:
            List of chunk dicts
        """
        chunks = []

        for section_name, section_text in sections.items():
            token_count = len(self.tokenizer.tokenize(section_text))

            if token_count > self.chunk_size:
                # Sub-chunk the section
                sub_chunks = self.chunk_by_tokens(section_text)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        "pmid": pmid,
                        "title": title,
                        "section": f"{section_name}_{i}",
                        "text": sub_chunk["text"],
                        "token_count": sub_chunk["token_count"],
                        "chunk_index": len(chunks)
                    })
            else:
                chunks.append({
                    "pmid": pmid,
                    "title": title,
                    "section": section_name,
                    "text": section_text,
                    "token_count": token_count,
                    "chunk_index": len(chunks)
                })

        return chunks

    def chunk_paper(
        self,
        pmid: str,
        title: str,
        abstract: str,
        full_text: Optional[str] = None
    ) -> List[dict]:
        """
        Create chunks for a paper.
        Uses abstract if full text not available.
        """
        chunks = []

        # Always include abstract as first chunk
        if abstract:
            abstract_tokens = len(self.tokenizer.tokenize(abstract))
            chunks.append({
                "pmid": pmid,
                "title": title,
                "section": "abstract",
                "text": abstract,
                "token_count": abstract_tokens,
                "chunk_index": 0
            })

        # Chunk full text if available
        if full_text:
            text_chunks = self.chunk_by_tokens(full_text)
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "pmid": pmid,
                    "title": title,
                    "section": f"body_{i}",
                    "text": chunk["text"],
                    "token_count": chunk["token_count"],
                    "chunk_index": len(chunks)
                })

        return chunks


@lru_cache(maxsize=1)
def get_embedding_generator() -> EmbeddingGenerator:
    """Get singleton embedding generator instance"""
    return EmbeddingGenerator()


@lru_cache(maxsize=1)
def get_text_chunker() -> TextChunker:
    """Get singleton text chunker instance"""
    return TextChunker()
