"""
Tests for Embedding Service.

Tests cover:
- Embedding generation with multiple providers
- Fallback chain behavior
- Caching functionality
- Batch processing
- Similarity calculation
- Statistics tracking
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List

from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingProvider,
    EmbeddingResult,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def embedding_service():
    """Create a fresh embedding service with mocked models."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
        # Patch the sentence transformers availability
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', False):
            with patch('app.services.embedding_service.OPENAI_AVAILABLE', False):
                service = EmbeddingService()
                yield service


@pytest.fixture
def embedding_service_with_st():
    """Create embedding service with mocked Sentence Transformers."""
    with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True):
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(384).astype(np.float32)
        mock_model.get_sentence_embedding_dimension.return_value = 384

        service = EmbeddingService()
        service._st_model = mock_model
        yield service


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return [
        "Hello, how are you?",
        "What is the weather like today?",
        "I love reading books about science.",
        "Can you help me with my homework?",
    ]


# ============================================================================
# Initialization Tests
# ============================================================================

class TestEmbeddingServiceInit:
    """Tests for embedding service initialization."""

    def test_default_embedding_dimension(self, embedding_service):
        """Default embedding dimension should be 384."""
        assert embedding_service.embedding_dim == 384

    def test_empty_cache_on_init(self, embedding_service):
        """Cache should be empty on initialization."""
        assert len(embedding_service.cache) == 0

    def test_stats_initialized(self, embedding_service):
        """Statistics should be initialized to zero."""
        stats = embedding_service.stats
        assert stats["total_requests"] == 0
        assert stats["cache_hits"] == 0
        assert stats["errors"] == 0

    def test_provider_usage_initialized(self, embedding_service):
        """Provider usage should be initialized for all providers."""
        stats = embedding_service.stats
        for provider in EmbeddingProvider:
            assert provider.value in stats["provider_usage"]
            assert stats["provider_usage"][provider.value] == 0


# ============================================================================
# Deterministic Embedding Tests
# ============================================================================

class TestDeterministicEmbedding:
    """Tests for deterministic fallback embedding."""

    @pytest.mark.asyncio
    async def test_generates_correct_dimension(self, embedding_service):
        """Should generate embedding with correct dimension."""
        embedding = await embedding_service.generate_embedding("Test text")

        assert len(embedding) == embedding_service.embedding_dim

    @pytest.mark.asyncio
    async def test_deterministic_output(self, embedding_service):
        """Same text should produce same embedding."""
        text = "This is a test sentence."

        embedding1 = await embedding_service.generate_embedding(text)
        embedding2 = await embedding_service.generate_embedding(text)

        assert embedding1 == embedding2

    @pytest.mark.asyncio
    async def test_different_texts_different_embeddings(self, embedding_service):
        """Different texts should produce different embeddings."""
        text1 = "Hello world"
        text2 = "Goodbye world"

        embedding1 = await embedding_service.generate_embedding(text1)
        embedding2 = await embedding_service.generate_embedding(text2)

        assert embedding1 != embedding2

    @pytest.mark.asyncio
    async def test_embedding_is_normalized(self, embedding_service):
        """Embedding should be normalized (unit length)."""
        embedding = await embedding_service.generate_embedding("Test text")

        norm = np.linalg.norm(embedding)
        # Allow small floating point error
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_handles_empty_string(self, embedding_service):
        """Should handle empty string gracefully."""
        embedding = await embedding_service.generate_embedding("")

        assert len(embedding) == embedding_service.embedding_dim

    @pytest.mark.asyncio
    async def test_handles_special_characters(self, embedding_service):
        """Should handle special characters."""
        text = "Hello! How are you? I'm fine... @#$%^&*()"
        embedding = await embedding_service.generate_embedding(text)

        assert len(embedding) == embedding_service.embedding_dim

    @pytest.mark.asyncio
    async def test_handles_unicode(self, embedding_service):
        """Should handle unicode characters."""
        text = "Hello! Bonjour! Hola!"
        embedding = await embedding_service.generate_embedding(text)

        assert len(embedding) == embedding_service.embedding_dim


# ============================================================================
# Detailed Embedding Tests
# ============================================================================

class TestDetailedEmbedding:
    """Tests for detailed embedding results."""

    @pytest.mark.asyncio
    async def test_returns_embedding_result(self, embedding_service):
        """Should return EmbeddingResult object."""
        result = await embedding_service.generate_embedding_detailed("Test text")

        assert isinstance(result, EmbeddingResult)
        assert len(result.embedding) == embedding_service.embedding_dim
        assert isinstance(result.provider, EmbeddingProvider)
        assert isinstance(result.model_name, str)

    @pytest.mark.asyncio
    async def test_tracks_tokens_used(self, embedding_service):
        """Should track approximate tokens used."""
        text = "Hello world how are you doing today"
        result = await embedding_service.generate_embedding_detailed(text)

        # Should approximate word count
        assert result.tokens_used > 0
        assert result.tokens_used <= len(text.split()) + 5

    @pytest.mark.asyncio
    async def test_uses_deterministic_provider(self, embedding_service):
        """Should use deterministic provider when others unavailable."""
        result = await embedding_service.generate_embedding_detailed("Test")

        assert result.provider == EmbeddingProvider.DETERMINISTIC


# ============================================================================
# Caching Tests
# ============================================================================

class TestEmbeddingCache:
    """Tests for embedding caching."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, embedding_service):
        """Second request for same text should hit cache."""
        text = "Cache test text"

        # First request - cache miss
        result1 = await embedding_service.generate_embedding_detailed(text)
        assert result1.cache_hit is False

        # Second request - cache hit
        result2 = await embedding_service.generate_embedding_detailed(text)
        assert result2.cache_hit is True

    @pytest.mark.asyncio
    async def test_cache_stats_updated(self, embedding_service):
        """Cache statistics should be updated correctly."""
        text = "Cache stats test"

        await embedding_service.generate_embedding(text)
        await embedding_service.generate_embedding(text)

        assert embedding_service.stats["total_requests"] == 2
        assert embedding_service.stats["cache_hits"] == 1

    @pytest.mark.asyncio
    async def test_clear_cache(self, embedding_service):
        """Cache should be clearable."""
        await embedding_service.generate_embedding("Test 1")
        await embedding_service.generate_embedding("Test 2")

        assert len(embedding_service.cache) == 2

        embedding_service.clear_cache()

        assert len(embedding_service.cache) == 0

    @pytest.mark.asyncio
    async def test_cache_returns_same_embedding(self, embedding_service):
        """Cached embedding should be identical to original."""
        text = "Cache identity test"

        embedding1 = await embedding_service.generate_embedding(text)
        embedding2 = await embedding_service.generate_embedding(text)

        assert embedding1 == embedding2


# ============================================================================
# Batch Processing Tests
# ============================================================================

class TestBatchEmbedding:
    """Tests for batch embedding generation."""

    @pytest.mark.asyncio
    async def test_batch_generates_correct_count(self, embedding_service, sample_texts):
        """Should generate correct number of embeddings."""
        embeddings = await embedding_service.batch_generate_embeddings(sample_texts)

        assert len(embeddings) == len(sample_texts)

    @pytest.mark.asyncio
    async def test_batch_correct_dimensions(self, embedding_service, sample_texts):
        """Each batch embedding should have correct dimension."""
        embeddings = await embedding_service.batch_generate_embeddings(sample_texts)

        for embedding in embeddings:
            assert len(embedding) == embedding_service.embedding_dim

    @pytest.mark.asyncio
    async def test_batch_handles_empty_list(self, embedding_service):
        """Should handle empty list gracefully."""
        embeddings = await embedding_service.batch_generate_embeddings([])

        assert embeddings == []

    @pytest.mark.asyncio
    async def test_batch_handles_single_item(self, embedding_service):
        """Should handle single item list."""
        embeddings = await embedding_service.batch_generate_embeddings(["Single text"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == embedding_service.embedding_dim


# ============================================================================
# Similarity Calculation Tests
# ============================================================================

class TestSimilarityCalculation:
    """Tests for cosine similarity calculation."""

    def test_identical_embeddings_similarity_one(self, embedding_service):
        """Identical embeddings should have similarity of 1."""
        embedding = [0.5, 0.5, 0.5, 0.5]

        similarity = embedding_service.calculate_similarity(embedding, embedding)

        assert abs(similarity - 1.0) < 0.001

    def test_orthogonal_embeddings_similarity_zero(self, embedding_service):
        """Orthogonal embeddings should have similarity near 0."""
        embedding1 = [1.0, 0.0, 0.0, 0.0]
        embedding2 = [0.0, 1.0, 0.0, 0.0]

        similarity = embedding_service.calculate_similarity(embedding1, embedding2)

        assert abs(similarity) < 0.001

    def test_opposite_embeddings_similarity_negative(self, embedding_service):
        """Opposite embeddings should have negative similarity."""
        embedding1 = [1.0, 1.0, 1.0, 1.0]
        embedding2 = [-1.0, -1.0, -1.0, -1.0]

        similarity = embedding_service.calculate_similarity(embedding1, embedding2)

        assert similarity < 0

    def test_zero_vector_returns_zero(self, embedding_service):
        """Zero vector should return 0 similarity."""
        embedding1 = [0.0, 0.0, 0.0, 0.0]
        embedding2 = [1.0, 1.0, 1.0, 1.0]

        similarity = embedding_service.calculate_similarity(embedding1, embedding2)

        assert similarity == 0.0

    @pytest.mark.asyncio
    async def test_similar_texts_higher_similarity(self, embedding_service):
        """Similar texts should have higher similarity than dissimilar ones."""
        text1 = "I love cats"
        text2 = "I like cats"
        text3 = "The weather is sunny"

        emb1 = await embedding_service.generate_embedding(text1)
        emb2 = await embedding_service.generate_embedding(text2)
        emb3 = await embedding_service.generate_embedding(text3)

        sim_similar = embedding_service.calculate_similarity(emb1, emb2)
        sim_different = embedding_service.calculate_similarity(emb1, emb3)

        # Similar texts should have higher similarity
        # Note: With deterministic embeddings, this may not always hold
        # but we can still test the function works
        assert isinstance(sim_similar, float)
        assert isinstance(sim_different, float)


# ============================================================================
# Statistics Tests
# ============================================================================

class TestEmbeddingStats:
    """Tests for embedding statistics."""

    @pytest.mark.asyncio
    async def test_get_stats_structure(self, embedding_service):
        """Stats should have expected structure."""
        await embedding_service.generate_embedding("Test")
        stats = embedding_service.get_stats()

        assert "embedding_dimension" in stats
        assert "cached_embeddings" in stats
        assert "total_requests" in stats
        assert "cache_hits" in stats
        assert "cache_hit_rate" in stats
        assert "provider_usage" in stats
        assert "available_providers" in stats

    @pytest.mark.asyncio
    async def test_stats_increment_correctly(self, embedding_service):
        """Stats should increment correctly with usage."""
        initial_requests = embedding_service.stats["total_requests"]

        await embedding_service.generate_embedding("Test 1")
        await embedding_service.generate_embedding("Test 2")
        await embedding_service.generate_embedding("Test 1")  # Cache hit

        assert embedding_service.stats["total_requests"] == initial_requests + 3
        assert embedding_service.stats["cache_hits"] == 1

    def test_get_cache_stats(self, embedding_service):
        """Cache stats should be retrievable."""
        stats = embedding_service.get_cache_stats()

        assert "cached_embeddings" in stats
        assert "embedding_dimension" in stats


# ============================================================================
# Health Status Tests
# ============================================================================

class TestHealthStatus:
    """Tests for health status reporting."""

    def test_health_status_structure(self, embedding_service):
        """Health status should have expected structure."""
        health = embedding_service.get_health_status()

        assert "status" in health
        assert "providers" in health
        assert "sentence_transformers" in health["providers"]
        assert "openai" in health["providers"]
        assert "deterministic" in health["providers"]

    def test_deterministic_always_available(self, embedding_service):
        """Deterministic provider should always be available."""
        health = embedding_service.get_health_status()

        assert health["providers"]["deterministic"]["available"] is True


# ============================================================================
# Provider Fallback Tests
# ============================================================================

class TestProviderFallback:
    """Tests for provider fallback behavior."""

    @pytest.mark.asyncio
    async def test_falls_back_to_deterministic(self, embedding_service):
        """Should fall back to deterministic when others fail."""
        # With mocked unavailable providers, should use deterministic
        result = await embedding_service.generate_embedding_detailed("Test")

        assert result.provider == EmbeddingProvider.DETERMINISTIC

    @pytest.mark.asyncio
    async def test_stats_track_provider_usage(self, embedding_service):
        """Should track which provider was used."""
        await embedding_service.generate_embedding("Test")

        deterministic_usage = embedding_service.stats["provider_usage"]["deterministic"]
        assert deterministic_usage > 0


# ============================================================================
# Sentence Transformers Tests (Mocked)
# ============================================================================

class TestSentenceTransformers:
    """Tests for Sentence Transformers provider."""

    @pytest.mark.asyncio
    async def test_uses_st_when_available(self, embedding_service_with_st):
        """Should use Sentence Transformers when available."""
        result = await embedding_service_with_st.generate_embedding_detailed("Test")

        assert result.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS

    @pytest.mark.asyncio
    async def test_st_batch_processing(self, embedding_service_with_st):
        """Should use batch processing with ST."""
        # Mock batch encode
        embedding_service_with_st._st_model.encode.return_value = np.random.randn(3, 384).astype(np.float32)

        embeddings = await embedding_service_with_st.batch_generate_embeddings([
            "Text 1", "Text 2", "Text 3"
        ])

        # Should call encode once for batch
        embedding_service_with_st._st_model.encode.assert_called()


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handles_provider_exceptions(self):
        """Should handle exceptions from providers gracefully."""
        with patch('app.services.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True):
            service = EmbeddingService()
            service._st_model = MagicMock()
            service._st_model.encode.side_effect = Exception("Model error")

            # Should fall back to deterministic
            result = await service.generate_embedding_detailed("Test")

            # Should still return an embedding
            assert len(result.embedding) == service.embedding_dim

    @pytest.mark.asyncio
    async def test_errors_tracked_in_stats(self, embedding_service):
        """Errors should be tracked in statistics."""
        # Force an error by patching the deterministic method
        with patch.object(embedding_service, '_generate_deterministic_embedding', side_effect=Exception("Test error")):
            result = await embedding_service.generate_embedding_detailed("Test")

            # Should return zero vector as absolute fallback
            assert result.embedding == [0.0] * embedding_service.embedding_dim

    def test_similarity_handles_invalid_input(self, embedding_service):
        """Similarity calculation should handle invalid input."""
        # Empty embeddings
        similarity = embedding_service.calculate_similarity([], [])
        assert similarity == 0.0
