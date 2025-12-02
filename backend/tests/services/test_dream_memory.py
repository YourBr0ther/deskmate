"""
Tests for Dream Memory Service.

Tests cover:
- Dream entry creation and storage
- Dream retrieval by ID and recency
- Dream search with semantic similarity
- Cleanup of expired dreams
- Statistics calculation
- Cleanup task lifecycle
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.dream_memory import DreamMemoryService, DreamEntry


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def dream_memory_service():
    """Create a fresh dream memory service instance."""
    with patch('app.services.dream_memory.config') as mock_config:
        mock_config.idle.dream_expiration_hours = 24
        service = DreamMemoryService()
        yield service


@pytest.fixture
def sample_dream_data():
    """Create sample dream data."""
    return {
        "action_type": "move",
        "content": "Walked to the window to look outside",
        "action_data": {"target": {"x": 50, "y": 8}},
        "room_state": {"objects_count": 15, "time_of_day": "night"},
        "assistant_position": {"x": 30, "y": 10},
        "success": True,
        "reasoning": "It's nighttime, wanted to observe the outside"
    }


@pytest.fixture
def mock_qdrant_results():
    """Create mock Qdrant search results."""
    return [
        {
            "id": "dream_001",
            "score": 0.95,
            "metadata": {
                "id": "dream_001",
                "action_type": "move",
                "content": "Walked to window",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=20)).isoformat(),
                "success": True
            }
        },
        {
            "id": "dream_002",
            "score": 0.85,
            "metadata": {
                "id": "dream_002",
                "action_type": "interact",
                "content": "Turned on the lamp",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=18)).isoformat(),
                "success": True
            }
        }
    ]


# ============================================================================
# DreamEntry Tests
# ============================================================================

class TestDreamEntry:
    """Tests for DreamEntry class."""

    def test_dream_entry_creation(self, sample_dream_data):
        """Should create dream entry with correct fields."""
        entry = DreamEntry(**sample_dream_data)

        assert entry.action_type == "move"
        assert entry.content == "Walked to the window to look outside"
        assert entry.success is True
        assert entry.id is not None
        assert entry.created_at is not None
        assert entry.expires_at is not None

    def test_dream_entry_expiration(self, sample_dream_data):
        """Should set expiration based on config."""
        with patch('app.services.dream_memory.config') as mock_config:
            mock_config.idle.dream_expiration_hours = 48

            entry = DreamEntry(**sample_dream_data)

            time_diff = entry.expires_at - entry.created_at
            assert time_diff.total_seconds() == 48 * 3600

    def test_dream_entry_to_dict(self, sample_dream_data):
        """Should convert to dict correctly."""
        entry = DreamEntry(**sample_dream_data)
        result = entry.to_dict()

        assert "id" in result
        assert result["action_type"] == "move"
        assert result["content"] == sample_dream_data["content"]
        assert result["is_dream"] is True
        assert "created_at" in result
        assert "expires_at" in result

    def test_dream_entry_unique_id(self, sample_dream_data):
        """Should generate unique IDs."""
        entry1 = DreamEntry(**sample_dream_data)
        entry2 = DreamEntry(**sample_dream_data)

        assert entry1.id != entry2.id


# ============================================================================
# Store Dream Tests
# ============================================================================

class TestStoreDream:
    """Tests for storing dreams."""

    @pytest.mark.asyncio
    async def test_store_dream_success(self, dream_memory_service, sample_dream_data):
        """Should store dream and return ID."""
        with patch('app.services.dream_memory.embedding_service') as mock_embed:
            mock_embed.embed_text = AsyncMock(return_value=[0.1] * 384)

            with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
                mock_qdrant.add_memories = AsyncMock()

                dream_id = await dream_memory_service.store_dream(**sample_dream_data)

                assert dream_id is not None
                mock_embed.embed_text.assert_called_once_with(sample_dream_data["content"])
                mock_qdrant.add_memories.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_dream_generates_embedding(self, dream_memory_service, sample_dream_data):
        """Should generate embedding for content."""
        with patch('app.services.dream_memory.embedding_service') as mock_embed:
            mock_embed.embed_text = AsyncMock(return_value=[0.1] * 384)

            with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
                mock_qdrant.add_memories = AsyncMock()

                await dream_memory_service.store_dream(**sample_dream_data)

                mock_embed.embed_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_dream_includes_metadata(self, dream_memory_service, sample_dream_data):
        """Should include full metadata in storage."""
        with patch('app.services.dream_memory.embedding_service') as mock_embed:
            mock_embed.embed_text = AsyncMock(return_value=[0.1] * 384)

            with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
                mock_qdrant.add_memories = AsyncMock()

                await dream_memory_service.store_dream(**sample_dream_data)

                call_args = mock_qdrant.add_memories.call_args
                memory_data = call_args[1]["memories"][0]
                assert "metadata" in memory_data
                assert memory_data["metadata"]["action_type"] == "move"
                assert memory_data["metadata"]["is_dream"] is True

    @pytest.mark.asyncio
    async def test_store_dream_error_handling(self, dream_memory_service, sample_dream_data):
        """Should raise on storage error."""
        with patch('app.services.dream_memory.embedding_service') as mock_embed:
            mock_embed.embed_text = AsyncMock(side_effect=Exception("Embedding error"))

            with pytest.raises(Exception):
                await dream_memory_service.store_dream(**sample_dream_data)


# ============================================================================
# Get Recent Dreams Tests
# ============================================================================

class TestGetRecentDreams:
    """Tests for getting recent dreams."""

    @pytest.mark.asyncio
    async def test_get_recent_dreams_success(self, dream_memory_service, mock_qdrant_results):
        """Should return recent dreams."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=mock_qdrant_results)

            dreams = await dream_memory_service.get_recent_dreams(limit=10)

            assert len(dreams) == 2
            assert dreams[0]["action_type"] in ["move", "interact"]

    @pytest.mark.asyncio
    async def test_get_recent_dreams_respects_limit(self, dream_memory_service, mock_qdrant_results):
        """Should respect limit parameter."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=mock_qdrant_results)

            await dream_memory_service.get_recent_dreams(limit=5)

            call_args = mock_qdrant.search_memories.call_args
            assert call_args[1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_get_recent_dreams_respects_hours_back(self, dream_memory_service):
        """Should filter by time window."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=[])

            await dream_memory_service.get_recent_dreams(hours_back=12)

            call_args = mock_qdrant.search_memories.call_args
            assert "filter_dict" in call_args[1]
            assert "created_at" in call_args[1]["filter_dict"]

    @pytest.mark.asyncio
    async def test_get_recent_dreams_empty(self, dream_memory_service):
        """Should return empty list when no dreams."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=[])

            dreams = await dream_memory_service.get_recent_dreams()

            assert dreams == []

    @pytest.mark.asyncio
    async def test_get_recent_dreams_error_handling(self, dream_memory_service):
        """Should return empty list on error."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(side_effect=Exception("DB error"))

            dreams = await dream_memory_service.get_recent_dreams()

            assert dreams == []


# ============================================================================
# Search Relevant Dreams Tests
# ============================================================================

class TestSearchRelevantDreams:
    """Tests for semantic dream search."""

    @pytest.mark.asyncio
    async def test_search_dreams_success(self, dream_memory_service, mock_qdrant_results):
        """Should return relevant dreams."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=mock_qdrant_results)

            dreams = await dream_memory_service.search_relevant_dreams("window")

            assert len(dreams) == 2
            assert all("relevance_score" in d for d in dreams)

    @pytest.mark.asyncio
    async def test_search_dreams_filters_by_score(self, dream_memory_service):
        """Should filter by minimum score."""
        results = [
            {"id": "1", "score": 0.9, "metadata": {"content": "High score"}},
            {"id": "2", "score": 0.5, "metadata": {"content": "Low score"}}
        ]

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=results)

            dreams = await dream_memory_service.search_relevant_dreams("test", min_score=0.7)

            assert len(dreams) == 1
            assert dreams[0]["relevance_score"] == 0.9

    @pytest.mark.asyncio
    async def test_search_dreams_respects_limit(self, dream_memory_service, mock_qdrant_results):
        """Should respect limit parameter."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=mock_qdrant_results)

            await dream_memory_service.search_relevant_dreams("test", limit=3)

            call_args = mock_qdrant.search_memories.call_args
            assert call_args[1]["limit"] == 3

    @pytest.mark.asyncio
    async def test_search_dreams_error_handling(self, dream_memory_service):
        """Should return empty list on error."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(side_effect=Exception("Search error"))

            dreams = await dream_memory_service.search_relevant_dreams("test")

            assert dreams == []


# ============================================================================
# Get Dream by ID Tests
# ============================================================================

class TestGetDreamById:
    """Tests for getting dream by ID."""

    @pytest.mark.asyncio
    async def test_get_dream_success(self, dream_memory_service):
        """Should return dream by ID."""
        mock_result = {
            "id": "dream_001",
            "metadata": {"id": "dream_001", "content": "Test dream"}
        }

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.get_memory_by_id = AsyncMock(return_value=mock_result)

            dream = await dream_memory_service.get_dream_by_id("dream_001")

            assert dream is not None
            assert dream["id"] == "dream_001"

    @pytest.mark.asyncio
    async def test_get_dream_not_found(self, dream_memory_service):
        """Should return None for nonexistent dream."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.get_memory_by_id = AsyncMock(return_value=None)

            dream = await dream_memory_service.get_dream_by_id("nonexistent")

            assert dream is None

    @pytest.mark.asyncio
    async def test_get_dream_error_handling(self, dream_memory_service):
        """Should return None on error."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.get_memory_by_id = AsyncMock(side_effect=Exception("DB error"))

            dream = await dream_memory_service.get_dream_by_id("dream_001")

            assert dream is None


# ============================================================================
# Cleanup Expired Dreams Tests
# ============================================================================

class TestCleanupExpiredDreams:
    """Tests for expired dream cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_expired(self, dream_memory_service):
        """Should remove expired dreams."""
        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        valid_time = (datetime.utcnow() + timedelta(hours=10)).isoformat()

        results = [
            {"metadata": {"id": "expired_1", "expires_at": expired_time}},
            {"metadata": {"id": "valid_1", "expires_at": valid_time}}
        ]

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=results)
            mock_qdrant.delete_memories = AsyncMock()

            count = await dream_memory_service.cleanup_expired_dreams()

            assert count == 1
            mock_qdrant.delete_memories.assert_called_once()
            call_args = mock_qdrant.delete_memories.call_args
            assert "expired_1" in call_args[1]["memory_ids"]
            assert "valid_1" not in call_args[1]["memory_ids"]

    @pytest.mark.asyncio
    async def test_cleanup_no_expired(self, dream_memory_service):
        """Should handle no expired dreams."""
        valid_time = (datetime.utcnow() + timedelta(hours=10)).isoformat()
        results = [{"metadata": {"id": "valid_1", "expires_at": valid_time}}]

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=results)
            mock_qdrant.delete_memories = AsyncMock()

            count = await dream_memory_service.cleanup_expired_dreams()

            assert count == 0
            mock_qdrant.delete_memories.assert_not_called()

    @pytest.mark.asyncio
    async def test_cleanup_handles_invalid_dates(self, dream_memory_service):
        """Should handle invalid date formats."""
        results = [
            {"metadata": {"id": "invalid_1", "expires_at": "not-a-date"}}
        ]

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=results)
            mock_qdrant.delete_memories = AsyncMock()

            count = await dream_memory_service.cleanup_expired_dreams()

            assert count == 1

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self, dream_memory_service):
        """Should return 0 on error."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(side_effect=Exception("DB error"))

            count = await dream_memory_service.cleanup_expired_dreams()

            assert count == 0


# ============================================================================
# Dream Statistics Tests
# ============================================================================

class TestDreamStatistics:
    """Tests for dream statistics."""

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, dream_memory_service, mock_qdrant_results):
        """Should return dream statistics."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=mock_qdrant_results)

            stats = await dream_memory_service.get_dream_statistics()

            assert "total_dreams_24h" in stats
            assert "successful_actions" in stats
            assert "failed_actions" in stats
            assert "success_rate" in stats
            assert "action_types" in stats
            assert "last_dream" in stats

    @pytest.mark.asyncio
    async def test_statistics_calculates_success_rate(self, dream_memory_service):
        """Should calculate success rate correctly."""
        results = [
            {"metadata": {"success": True, "action_type": "move"}},
            {"metadata": {"success": True, "action_type": "move"}},
            {"metadata": {"success": False, "action_type": "interact"}}
        ]

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=results)

            stats = await dream_memory_service.get_dream_statistics()

            assert stats["total_dreams_24h"] == 3
            assert stats["successful_actions"] == 2
            assert stats["failed_actions"] == 1
            assert abs(stats["success_rate"] - 0.667) < 0.01

    @pytest.mark.asyncio
    async def test_statistics_counts_action_types(self, dream_memory_service):
        """Should count action types."""
        results = [
            {"metadata": {"success": True, "action_type": "move"}},
            {"metadata": {"success": True, "action_type": "move"}},
            {"metadata": {"success": True, "action_type": "interact"}}
        ]

        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=results)

            stats = await dream_memory_service.get_dream_statistics()

            assert stats["action_types"]["move"] == 2
            assert stats["action_types"]["interact"] == 1

    @pytest.mark.asyncio
    async def test_statistics_empty_dreams(self, dream_memory_service):
        """Should handle empty dreams list."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(return_value=[])

            stats = await dream_memory_service.get_dream_statistics()

            assert stats["total_dreams_24h"] == 0
            assert stats["success_rate"] == 0
            assert stats["last_dream"] is None

    @pytest.mark.asyncio
    async def test_statistics_error_handling(self, dream_memory_service):
        """Should return default stats on error."""
        with patch('app.services.dream_memory.qdrant_manager') as mock_qdrant:
            mock_qdrant.search_memories = AsyncMock(side_effect=Exception("DB error"))

            stats = await dream_memory_service.get_dream_statistics()

            assert stats["total_dreams_24h"] == 0
            assert stats["success_rate"] == 0


# ============================================================================
# Cleanup Task Lifecycle Tests
# ============================================================================

class TestCleanupTaskLifecycle:
    """Tests for cleanup task start/stop."""

    @pytest.mark.asyncio
    async def test_start_cleanup_task(self, dream_memory_service):
        """Should start cleanup task."""
        with patch.object(dream_memory_service, '_cleanup_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.return_value = None

            await dream_memory_service.start_cleanup_task()

            assert dream_memory_service._cleanup_task is not None

            # Cleanup
            if dream_memory_service._cleanup_task:
                dream_memory_service._cleanup_task.cancel()
                try:
                    await dream_memory_service._cleanup_task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_stop_cleanup_task(self, dream_memory_service):
        """Should stop cleanup task."""
        # Create a task that runs forever
        async def forever_loop():
            while True:
                await asyncio.sleep(10)

        dream_memory_service._cleanup_task = asyncio.create_task(forever_loop())

        await dream_memory_service.stop_cleanup_task()

        assert dream_memory_service._cleanup_task.cancelled() or dream_memory_service._cleanup_task.done()

    @pytest.mark.asyncio
    async def test_stop_when_no_task(self, dream_memory_service):
        """Should handle stopping when no task exists."""
        dream_memory_service._cleanup_task = None

        # Should not raise
        await dream_memory_service.stop_cleanup_task()

    @pytest.mark.asyncio
    async def test_start_replaces_done_task(self, dream_memory_service):
        """Should replace completed task on start."""
        # Create a task that's already done
        async def done_task():
            return None

        dream_memory_service._cleanup_task = asyncio.create_task(done_task())
        await dream_memory_service._cleanup_task

        with patch.object(dream_memory_service, '_cleanup_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.return_value = None

            await dream_memory_service.start_cleanup_task()

            # Should have created new task
            assert dream_memory_service._cleanup_task is not None

            # Cleanup
            if dream_memory_service._cleanup_task and not dream_memory_service._cleanup_task.done():
                dream_memory_service._cleanup_task.cancel()
                try:
                    await dream_memory_service._cleanup_task
                except asyncio.CancelledError:
                    pass

