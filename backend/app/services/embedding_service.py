"""
Embedding Service for generating text embeddings.

This service provides text embedding generation for conversation memory.
Currently uses a simple approach but can be extended with proper embedding models.
"""

import logging
import hashlib
import numpy as np
from typing import List, Optional
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        self.embedding_dim = 1536  # OpenAI embedding dimension
        self.cache = {}  # Simple in-memory cache for embeddings

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        TODO: Replace with proper embedding model like:
        - OpenAI text-embedding-ada-002
        - Sentence Transformers
        - Local BERT/RoBERTa models
        """
        try:
            # Check cache first
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.cache:
                return self.cache[text_hash]

            # For now, create a deterministic but varied embedding
            # This ensures same text always gets same embedding
            embedding = self._create_deterministic_embedding(text)

            # Cache the result
            self.cache[text_hash] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim

    def _create_deterministic_embedding(self, text: str) -> List[float]:
        """
        Create a deterministic embedding based on text content.

        This is a placeholder implementation that creates embeddings
        based on text characteristics. Replace with proper embedding model.
        """
        try:
            # Normalize text
            text_lower = text.lower().strip()

            # Create multiple hash seeds for different dimensions
            base_hash = hashlib.md5(text_lower.encode()).hexdigest()

            # Initialize embedding vector
            embedding = []

            # Generate embedding dimensions using various text features
            for i in range(0, self.embedding_dim, 64):  # Process in chunks of 64
                # Create a seed for this chunk
                chunk_seed = int(base_hash[i % 32:(i % 32) + 8] or "0", 16)
                np.random.seed(chunk_seed)

                # Generate chunk based on text features
                chunk = self._generate_embedding_chunk(text_lower, chunk_seed)
                embedding.extend(chunk[:min(64, self.embedding_dim - i)])

            # Ensure exactly the right dimension
            embedding = embedding[:self.embedding_dim]
            while len(embedding) < self.embedding_dim:
                embedding.append(0.0)

            # Normalize the vector
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = [x / norm for x in embedding]

            return embedding

        except Exception as e:
            logger.error(f"Error creating deterministic embedding: {e}")
            return [0.0] * self.embedding_dim

    def _generate_embedding_chunk(self, text: str, seed: int) -> List[float]:
        """Generate a 64-dimensional chunk based on text features."""
        np.random.seed(seed)

        # Base random vector
        chunk = np.random.randn(64).tolist()

        # Modify based on text characteristics
        text_features = {
            'length': len(text) / 1000.0,  # Normalized length
            'word_count': len(text.split()) / 100.0,  # Normalized word count
            'char_diversity': len(set(text)) / 100.0,  # Character diversity
            'vowel_ratio': sum(1 for c in text if c in 'aeiou') / max(len(text), 1),
            'question_mark': 1.0 if '?' in text else 0.0,
            'exclamation': 1.0 if '!' in text else 0.0,
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1)
        }

        # Apply text features to modify the embedding
        for i, (feature, value) in enumerate(text_features.items()):
            if i < len(chunk):
                chunk[i] = chunk[i] * (1 + value)

        return chunk

    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            tasks = [self.generate_embedding(text) for text in texts]
            embeddings = await asyncio.gather(*tasks)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            a = np.array(embedding1)
            b = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    def get_cache_stats(self) -> dict:
        """Get embedding cache statistics."""
        return {
            "cached_embeddings": len(self.cache),
            "embedding_dimension": self.embedding_dim
        }


# Global instance
embedding_service = EmbeddingService()