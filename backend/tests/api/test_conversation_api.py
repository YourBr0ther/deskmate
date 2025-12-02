"""
Tests for Conversation API endpoints.

Tests cover:
- GET /conversation/memory/stats - Memory statistics
- GET /conversation/memory/summary - Conversation summary
- POST /conversation/memory/clear - Clear current memory
- POST /conversation/memory/clear-all - Clear all memory
- POST /conversation/memory/clear-persona - Clear persona memory
- GET /conversation/history - Chat history
- POST /conversation/initialize - Initialize with persona
- POST /conversation/embeddings/generate - Generate embedding
- POST /conversation/embeddings/batch - Batch embeddings
- POST /conversation/embeddings/similarity - Calculate similarity
- GET /conversation/embeddings/stats - Embedding stats
- POST /conversation/embeddings/clear-cache - Clear cache
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.services.embedding_service import EmbeddingResult, EmbeddingProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_memory_stats():
    """Create mock memory stats."""
    return {
        "total_messages": 42,
        "conversation_id": "conv_12345",
        "persona_name": "Alice",
        "vector_count": 100
    }


@pytest.fixture
def mock_embedding_stats():
    """Create mock embedding stats."""
    return {
        "cache_size": 50,
        "cache_hits": 30,
        "cache_misses": 20,
        "hit_rate": 0.6
    }


@pytest.fixture
def mock_embedding_result():
    """Create mock embedding result."""
    return EmbeddingResult(
        embedding=[0.1] * 384,
        provider=EmbeddingProvider.NANO_GPT,
        model_name="text-embedding-3-small",
        tokens_used=10,
        cache_hit=False
    )


@pytest.fixture
def mock_chat_history():
    """Create mock chat history."""
    return [
        {"role": "user", "content": "Hello", "timestamp": "2024-01-01T12:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T12:00:01"}
    ]


# ============================================================================
# GET /conversation/memory/stats Tests
# ============================================================================

class TestGetMemoryStats:
    """Tests for GET /conversation/memory/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, client, mock_memory_stats, mock_embedding_stats):
        """Should return memory and embedding stats."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_stats.return_value = mock_memory_stats

            with patch('app.api.conversation.embedding_service') as mock_embed:
                mock_embed.get_cache_stats.return_value = mock_embedding_stats

                response = await client.get("/conversation/memory/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "memory" in data
                assert "embeddings" in data

    @pytest.mark.asyncio
    async def test_get_stats_error_handling(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_stats.side_effect = Exception("Stats error")

            response = await client.get("/conversation/memory/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data


# ============================================================================
# GET /conversation/memory/summary Tests
# ============================================================================

class TestGetConversationSummary:
    """Tests for GET /conversation/memory/summary endpoint."""

    @pytest.mark.asyncio
    async def test_get_summary_success(self, client):
        """Should return conversation summary."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_conversation_summary = AsyncMock(
                return_value="Discussed weather and plans for the day."
            )

            response = await client.get("/conversation/memory/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "summary" in data

    @pytest.mark.asyncio
    async def test_get_summary_error_handling(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_conversation_summary = AsyncMock(
                side_effect=Exception("Summary error")
            )

            response = await client.get("/conversation/memory/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


# ============================================================================
# POST /conversation/memory/clear Tests
# ============================================================================

class TestClearMemory:
    """Tests for POST /conversation/memory/clear endpoint."""

    @pytest.mark.asyncio
    async def test_clear_memory_success(self, client):
        """Should clear memory and return new conversation ID."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.initialize_conversation = AsyncMock(return_value="conv_new_123")

            response = await client.post("/conversation/memory/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["conversation_id"] == "conv_new_123"

    @pytest.mark.asyncio
    async def test_clear_memory_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.initialize_conversation = AsyncMock(
                side_effect=Exception("Clear error")
            )

            response = await client.post("/conversation/memory/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


# ============================================================================
# POST /conversation/memory/clear-all Tests
# ============================================================================

class TestClearAllMemory:
    """Tests for POST /conversation/memory/clear-all endpoint."""

    @pytest.mark.asyncio
    async def test_clear_all_success(self, client):
        """Should clear all memory including vector DB."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.clear_all_memory = AsyncMock(return_value=True)
            mock_memory.initialize_conversation = AsyncMock(return_value="conv_fresh")

            response = await client.post("/conversation/memory/clear-all")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "vector database" in data["message"]

    @pytest.mark.asyncio
    async def test_clear_all_failed(self, client):
        """Should return error when clear fails."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.clear_all_memory = AsyncMock(return_value=False)

            response = await client.post("/conversation/memory/clear-all")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


# ============================================================================
# POST /conversation/memory/clear-persona Tests
# ============================================================================

class TestClearPersonaMemory:
    """Tests for POST /conversation/memory/clear-persona endpoint."""

    @pytest.mark.asyncio
    async def test_clear_persona_success(self, client):
        """Should clear memory for specific persona."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.clear_persona_memory = AsyncMock(return_value=True)

            response = await client.post(
                "/conversation/memory/clear-persona",
                params={"persona_name": "Alice"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Alice" in data["message"]

    @pytest.mark.asyncio
    async def test_clear_persona_empty_name(self, client):
        """Should return error for empty persona name."""
        response = await client.post(
            "/conversation/memory/clear-persona",
            params={"persona_name": ""}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "required" in data["error"]

    @pytest.mark.asyncio
    async def test_clear_persona_failed(self, client):
        """Should return error when clear fails."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.clear_persona_memory = AsyncMock(return_value=False)

            response = await client.post(
                "/conversation/memory/clear-persona",
                params={"persona_name": "UnknownPersona"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


# ============================================================================
# GET /conversation/history Tests
# ============================================================================

class TestGetChatHistory:
    """Tests for GET /conversation/history endpoint."""

    @pytest.mark.asyncio
    async def test_get_history_success(self, client, mock_chat_history):
        """Should return chat history."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_chat_history_for_frontend = AsyncMock(
                return_value=mock_chat_history
            )

            response = await client.get("/conversation/history")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["messages"]) == 2
            assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_get_history_with_limit(self, client, mock_chat_history):
        """Should respect limit parameter."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_chat_history_for_frontend = AsyncMock(
                return_value=mock_chat_history[:1]
            )

            response = await client.get("/conversation/history", params={"limit": 1})

            assert response.status_code == 200
            data = response.json()
            assert len(data["messages"]) == 1

    @pytest.mark.asyncio
    async def test_get_history_empty(self, client):
        """Should return empty list when no history."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.get_chat_history_for_frontend = AsyncMock(return_value=[])

            response = await client.get("/conversation/history")

            assert response.status_code == 200
            data = response.json()
            assert data["messages"] == []
            assert data["count"] == 0


# ============================================================================
# POST /conversation/initialize Tests
# ============================================================================

class TestInitializeConversation:
    """Tests for POST /conversation/initialize endpoint."""

    @pytest.mark.asyncio
    async def test_initialize_success(self, client, mock_chat_history):
        """Should initialize conversation with persona."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.initialize_conversation = AsyncMock(return_value="conv_123")
            mock_memory.get_chat_history_for_frontend = AsyncMock(
                return_value=mock_chat_history
            )

            response = await client.post(
                "/conversation/initialize",
                json={"persona_name": "Alice", "load_history": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["conversation_id"] == "conv_123"
            assert data["persona_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_initialize_invalid_persona_name(self, client):
        """Should return error for invalid persona name."""
        response = await client.post(
            "/conversation/initialize",
            json={"persona_name": ""}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    @pytest.mark.asyncio
    async def test_initialize_no_history(self, client):
        """Should initialize without loading history."""
        with patch('app.api.conversation.conversation_memory') as mock_memory:
            mock_memory.initialize_conversation = AsyncMock(return_value="conv_456")
            mock_memory.get_chat_history_for_frontend = AsyncMock(return_value=[])

            response = await client.post(
                "/conversation/initialize",
                json={"persona_name": "Bob", "load_history": False}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


# ============================================================================
# POST /conversation/embeddings/generate Tests
# ============================================================================

class TestGenerateEmbedding:
    """Tests for POST /conversation/embeddings/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, client, mock_embedding_result):
        """Should generate embedding for text."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.generate_embedding_detailed = AsyncMock(
                return_value=mock_embedding_result
            )

            response = await client.post(
                "/conversation/embeddings/generate",
                json={"text": "Hello world"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "embedding" in data
            assert "metadata" in data
            assert data["metadata"]["embedding_dimension"] == 384

    @pytest.mark.asyncio
    async def test_generate_embedding_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.generate_embedding_detailed = AsyncMock(
                side_effect=Exception("Embedding error")
            )

            response = await client.post(
                "/conversation/embeddings/generate",
                json={"text": "Test"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


# ============================================================================
# POST /conversation/embeddings/batch Tests
# ============================================================================

class TestBatchEmbeddings:
    """Tests for POST /conversation/embeddings/batch endpoint."""

    @pytest.mark.asyncio
    async def test_batch_embeddings_success(self, client):
        """Should generate batch embeddings."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.batch_generate_embeddings = AsyncMock(
                return_value=[[0.1] * 384, [0.2] * 384]
            )

            response = await client.post(
                "/conversation/embeddings/batch",
                json={"texts": ["Hello", "World"]}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_batch_embeddings_empty(self, client):
        """Should handle empty batch."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.batch_generate_embeddings = AsyncMock(return_value=[])

            response = await client.post(
                "/conversation/embeddings/batch",
                json={"texts": []}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0


# ============================================================================
# POST /conversation/embeddings/similarity Tests
# ============================================================================

class TestCalculateSimilarity:
    """Tests for POST /conversation/embeddings/similarity endpoint."""

    @pytest.mark.asyncio
    async def test_similarity_success(self, client):
        """Should calculate similarity between texts."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.generate_embedding = AsyncMock(return_value=[0.5] * 384)
            mock_embed.calculate_similarity.return_value = 0.95

            response = await client.post(
                "/conversation/embeddings/similarity",
                json={"text1": "Hello", "text2": "Hi there"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["similarity"] == 0.95

    @pytest.mark.asyncio
    async def test_similarity_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.generate_embedding = AsyncMock(
                side_effect=Exception("Embedding failed")
            )

            response = await client.post(
                "/conversation/embeddings/similarity",
                json={"text1": "A", "text2": "B"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"


# ============================================================================
# GET /conversation/embeddings/stats Tests
# ============================================================================

class TestGetEmbeddingStats:
    """Tests for GET /conversation/embeddings/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, client, mock_embedding_stats):
        """Should return embedding stats."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.get_stats.return_value = mock_embedding_stats
            mock_embed.get_health_status.return_value = {"healthy": True}

            response = await client.get("/conversation/embeddings/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "stats" in data
            assert "health" in data


# ============================================================================
# POST /conversation/embeddings/clear-cache Tests
# ============================================================================

class TestClearEmbeddingCache:
    """Tests for POST /conversation/embeddings/clear-cache endpoint."""

    @pytest.mark.asyncio
    async def test_clear_cache_success(self, client):
        """Should clear embedding cache."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.clear_cache = MagicMock()

            response = await client.post("/conversation/embeddings/clear-cache")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            mock_embed.clear_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_error(self, client):
        """Should handle errors gracefully."""
        with patch('app.api.conversation.embedding_service') as mock_embed:
            mock_embed.clear_cache.side_effect = Exception("Clear failed")

            response = await client.post("/conversation/embeddings/clear-cache")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"

