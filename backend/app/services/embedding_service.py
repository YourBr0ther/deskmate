"""
Embedding Service for generating text embeddings.

This service provides text embedding generation for conversation memory using
multiple embedding providers with automatic fallback:
1. Sentence Transformers (primary - local, fast, private)
2. OpenAI embeddings (fallback - when local model fails)
3. Deterministic fallback (last resort - ensures system stability)
"""

import logging
import hashlib
import numpy as np
from typing import List, Optional, Dict, Any
import asyncio
import os
from dataclasses import dataclass
from enum import Enum
import time

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingProvider(Enum):
    """Available embedding providers."""
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OPENAI = "openai"
    DETERMINISTIC = "deterministic"


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    embedding: List[float]
    provider: EmbeddingProvider
    model_name: str
    tokens_used: int = 0
    cache_hit: bool = False


class EmbeddingService:
    """Service for generating text embeddings with multiple providers and fallback."""

    def __init__(self):
        self.embedding_dim = 384  # Updated to match sentence-transformers default
        self.cache = {}  # Simple in-memory cache for embeddings
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "provider_usage": {provider.value: 0 for provider in EmbeddingProvider},
            "total_tokens": 0,
            "errors": 0
        }

        # Sentence Transformers model
        self._st_model = None
        self._st_model_name = "all-MiniLM-L6-v2"  # Fast and efficient

        # OpenAI client
        self._openai_client = None
        self._openai_model = "text-embedding-3-small"  # Cost-effective

        # Initialize models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize available embedding models."""
        logger.info("Initializing embedding models...")

        # Initialize Sentence Transformers if available
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Deferring Sentence Transformers model loading: {self._st_model_name}")
                # Don't load the model at startup to avoid blocking
                # It will be loaded on first use
                self._st_model = None
                logger.info("Sentence Transformers will be loaded on first use")

            except Exception as e:
                logger.error(f"Failed to initialize Sentence Transformers: {e}")
                self._st_model = None
        else:
            logger.warning("Sentence Transformers not available - install with: pip install sentence-transformers")

        # Initialize OpenAI if available
        if OPENAI_AVAILABLE:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self._openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("OpenAI embeddings initialized successfully")
                else:
                    logger.info("OpenAI API key not found - OpenAI embeddings unavailable")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self._openai_client = None
        else:
            logger.warning("OpenAI not available - install with: pip install openai")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using the best available provider.

        Args:
            text: Text to embed

        Returns:
            List of float values representing the embedding
        """
        result = await self.generate_embedding_detailed(text)
        return result.embedding

    async def generate_embedding_detailed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding with detailed result information.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with embedding and metadata
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # Check cache first
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self.cache:
                self.stats["cache_hits"] += 1
                cached_result = self.cache[text_hash]
                cached_result.cache_hit = True
                return cached_result

            # Try providers in order of preference
            providers = [
                (EmbeddingProvider.SENTENCE_TRANSFORMERS, self._generate_st_embedding),
                (EmbeddingProvider.OPENAI, self._generate_openai_embedding),
                (EmbeddingProvider.DETERMINISTIC, self._generate_deterministic_embedding)
            ]

            for provider, method in providers:
                try:
                    result = await method(text)

                    # Update stats
                    self.stats["provider_usage"][provider.value] += 1
                    self.stats["total_tokens"] += result.tokens_used

                    # Cache the result
                    self.cache[text_hash] = result

                    # Log performance
                    duration = time.time() - start_time
                    logger.debug(f"Generated embedding using {provider.value} in {duration:.3f}s")

                    return result

                except Exception as e:
                    logger.warning(f"Provider {provider.value} failed: {e}")
                    continue

            # If all providers fail, this shouldn't happen due to deterministic fallback
            raise Exception("All embedding providers failed")

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to generate embedding: {e}")

            # Return zero vector as absolute fallback
            return EmbeddingResult(
                embedding=[0.0] * self.embedding_dim,
                provider=EmbeddingProvider.DETERMINISTIC,
                model_name="fallback",
                tokens_used=len(text.split())
            )

    async def _generate_st_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding using Sentence Transformers."""
        # Load model on first use if not already loaded
        if not self._st_model and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading Sentence Transformers model on first use: {self._st_model_name}")
                # Load model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self._st_model = await loop.run_in_executor(
                    None,
                    lambda: SentenceTransformer(self._st_model_name)
                )
                # Set embedding dimension based on model
                self.embedding_dim = self._st_model.get_sentence_embedding_dimension()
                logger.info(f"Sentence Transformers loaded successfully (dim: {self.embedding_dim})")
            except Exception as e:
                logger.error(f"Failed to load Sentence Transformers model: {e}")
                raise Exception(f"Sentence Transformers model loading failed: {e}")

        if not self._st_model:
            raise Exception("Sentence Transformers model not available")

        # Run embedding generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._st_model.encode(text, convert_to_numpy=True).tolist()
        )

        return EmbeddingResult(
            embedding=embedding,
            provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
            model_name=self._st_model_name,
            tokens_used=len(text.split())  # Approximate token count
        )

    async def _generate_openai_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding using OpenAI API."""
        if not self._openai_client:
            raise Exception("OpenAI client not available")

        try:
            response = await asyncio.to_thread(
                self._openai_client.embeddings.create,
                input=text,
                model=self._openai_model
            )

            embedding = response.data[0].embedding
            tokens_used = response.usage.total_tokens

            # Adjust embedding dimension if needed
            if len(embedding) != self.embedding_dim:
                if len(embedding) > self.embedding_dim:
                    embedding = embedding[:self.embedding_dim]
                else:
                    embedding.extend([0.0] * (self.embedding_dim - len(embedding)))

            return EmbeddingResult(
                embedding=embedding,
                provider=EmbeddingProvider.OPENAI,
                model_name=self._openai_model,
                tokens_used=tokens_used
            )

        except Exception as e:
            raise Exception(f"OpenAI embedding failed: {e}")

    async def _generate_deterministic_embedding(self, text: str) -> EmbeddingResult:
        """
        Generate deterministic embedding as fallback.

        This is the original implementation, kept for compatibility and as a fallback.
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

            return EmbeddingResult(
                embedding=embedding,
                provider=EmbeddingProvider.DETERMINISTIC,
                model_name="deterministic",
                tokens_used=len(text.split())
            )

        except Exception as e:
            logger.error(f"Error creating deterministic embedding: {e}")
            return EmbeddingResult(
                embedding=[0.0] * self.embedding_dim,
                provider=EmbeddingProvider.DETERMINISTIC,
                model_name="fallback",
                tokens_used=len(text.split())
            )

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
        """Generate embeddings for multiple texts efficiently."""
        try:
            # Use batch processing if available (Sentence Transformers)
            if self._st_model:
                return await self._batch_generate_st_embeddings(texts)

            # Otherwise, process individually
            tasks = [self.generate_embedding(text) for text in texts]
            embeddings = await asyncio.gather(*tasks)
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]

    async def _batch_generate_st_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch using Sentence Transformers."""
        if not self._st_model:
            raise Exception("Sentence Transformers model not available")

        # Run batch embedding generation in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._st_model.encode(texts, convert_to_numpy=True).tolist()
        )

        # Update stats
        for text in texts:
            self.stats["total_requests"] += 1
            self.stats["provider_usage"][EmbeddingProvider.SENTENCE_TRANSFORMERS.value] += 1
            self.stats["total_tokens"] += len(text.split())

        return embeddings

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

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive embedding service statistics."""
        cache_hit_rate = (self.stats["cache_hits"] / max(self.stats["total_requests"], 1)) * 100

        return {
            "embedding_dimension": self.embedding_dim,
            "cached_embeddings": len(self.cache),
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "provider_usage": self.stats["provider_usage"],
            "total_tokens_processed": self.stats["total_tokens"],
            "errors": self.stats["errors"],
            "available_providers": {
                "sentence_transformers": self._st_model is not None,
                "openai": self._openai_client is not None,
                "deterministic": True
            },
            "models": {
                "sentence_transformers": self._st_model_name if self._st_model else None,
                "openai": self._openai_model if self._openai_client else None
            }
        }

    def get_cache_stats(self) -> dict:
        """Get embedding cache statistics (legacy compatibility)."""
        return {
            "cached_embeddings": len(self.cache),
            "embedding_dimension": self.embedding_dim
        }

    def clear_cache(self):
        """Clear the embedding cache."""
        self.cache.clear()
        logger.info("Embedding cache cleared")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of embedding providers."""
        return {
            "status": "healthy" if (self._st_model or self._openai_client) else "degraded",
            "providers": {
                "sentence_transformers": {
                    "available": self._st_model is not None,
                    "model": self._st_model_name if self._st_model else None
                },
                "openai": {
                    "available": self._openai_client is not None,
                    "model": self._openai_model if self._openai_client else None
                },
                "deterministic": {
                    "available": True,
                    "model": "fallback"
                }
            }
        }


# Global instance
embedding_service = EmbeddingService()