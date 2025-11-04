"""
Tests for the Conversation Memory service.
Tests vector database integration and semantic search capabilities.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
import json

from app.services.conversation_memory import ConversationMemory, MemoryEntry
from app.db.qdrant import qdrant_client


@pytest.fixture
def conversation_memory():
    """Create a ConversationMemory instance for testing."""
    return ConversationMemory()


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    mock_client = Mock()
    mock_client.upsert = AsyncMock()
    mock_client.search = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.scroll = AsyncMock()
    return mock_client


@pytest.fixture
def sample_memory_entries():
    """Sample memory entries for testing."""
    return [
        MemoryEntry(
            id="mem1",
            content="User asked about turning on the lamp",
            embedding=[0.1, 0.2, 0.3],
            timestamp=datetime.now(),
            persona_name="Alice",
            memory_type="conversation",
            metadata={"action": "lamp_on", "object": "lamp_001"}
        ),
        MemoryEntry(
            id="mem2",
            content="Assistant moved to the desk area",
            embedding=[0.4, 0.5, 0.6],
            timestamp=datetime.now() - timedelta(hours=1),
            persona_name="Alice",
            memory_type="action",
            metadata={"action": "move", "position": {"x": 15, "y": 5}}
        ),
        MemoryEntry(
            id="mem3",
            content="User mentioned liking bright lighting",
            embedding=[0.1, 0.3, 0.5],
            timestamp=datetime.now() - timedelta(days=1),
            persona_name="Alice",
            memory_type="preference",
            metadata={"preference": "lighting", "value": "bright"}
        )
    ]


class TestConversationMemoryBasic:
    """Test basic memory operations."""

    @pytest.mark.asyncio
    async def test_store_memory_entry(self, conversation_memory, mock_qdrant_client):
        """Test storing a memory entry."""

        memory_entry = MemoryEntry(
            id="test_memory",
            content="Test memory content",
            embedding=[0.1, 0.2, 0.3],
            timestamp=datetime.now(),
            persona_name="Alice",
            memory_type="conversation"
        )

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert):

            result = await conversation_memory.store_memory(memory_entry)

            assert result is True
            mock_qdrant_client.upsert.assert_called_once()

            # Verify the upsert call contains correct data
            call_args = mock_qdrant_client.upsert.call_args
            assert call_args[1]['collection_name'] == 'conversation_memory'
            assert len(call_args[1]['points']) == 1

    @pytest.mark.asyncio
    async def test_store_memory_from_text(self, conversation_memory, mock_qdrant_client):
        """Test storing memory from text content."""

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            result = await conversation_memory.store_memory_from_text(
                content="User wants to turn on the lamp",
                persona_name="Alice",
                memory_type="conversation",
                metadata={"object": "lamp_001"}
            )

            assert result is True
            mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_relevant_memories(self, conversation_memory, mock_qdrant_client, sample_memory_entries):
        """Test searching for relevant memories."""

        # Mock search results
        mock_search_results = [
            Mock(id="mem1", score=0.9, payload={
                "content": sample_memory_entries[0].content,
                "timestamp": sample_memory_entries[0].timestamp.isoformat(),
                "persona_name": "Alice",
                "memory_type": "conversation",
                "metadata": sample_memory_entries[0].metadata
            }),
            Mock(id="mem2", score=0.7, payload={
                "content": sample_memory_entries[1].content,
                "timestamp": sample_memory_entries[1].timestamp.isoformat(),
                "persona_name": "Alice",
                "memory_type": "action",
                "metadata": sample_memory_entries[1].metadata
            })
        ]

        mock_qdrant_client.search.return_value = mock_search_results

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            results = await conversation_memory.search_relevant_memories(
                query="lamp lighting",
                persona_name="Alice",
                limit=5,
                min_score=0.5
            )

            assert len(results) == 2
            assert results[0]['content'] == sample_memory_entries[0].content
            assert results[0]['relevance'] == 0.9
            assert results[1]['content'] == sample_memory_entries[1].content
            assert results[1]['relevance'] == 0.7

            # Verify search was called with correct parameters
            mock_qdrant_client.search.assert_called_once()
            call_args = mock_qdrant_client.search.call_args
            assert call_args[1]['collection_name'] == 'conversation_memory'
            assert call_args[1]['limit'] == 5

    @pytest.mark.asyncio
    async def test_search_with_persona_filter(self, conversation_memory, mock_qdrant_client):
        """Test searching memories with persona filtering."""

        mock_qdrant_client.search.return_value = []

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            await conversation_memory.search_relevant_memories(
                query="test query",
                persona_name="Alice",
                limit=5
            )

            # Verify persona filter was applied
            call_args = mock_qdrant_client.search.call_args
            filters = call_args[1]['query_filter']
            assert filters is not None


class TestConversationMemoryAdvanced:
    """Test advanced memory operations."""

    @pytest.mark.asyncio
    async def test_search_by_memory_type(self, conversation_memory, mock_qdrant_client):
        """Test searching memories by type."""

        mock_qdrant_client.search.return_value = []

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            await conversation_memory.search_memories_by_type(
                memory_type="preference",
                persona_name="Alice",
                limit=10
            )

            # Verify type filter was applied
            call_args = mock_qdrant_client.search.call_args
            filters = call_args[1]['query_filter']
            assert filters is not None

    @pytest.mark.asyncio
    async def test_search_recent_memories(self, conversation_memory, mock_qdrant_client):
        """Test searching recent memories within time window."""

        mock_qdrant_client.search.return_value = []

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            await conversation_memory.search_recent_memories(
                query="recent activity",
                persona_name="Alice",
                hours_back=24,
                limit=5
            )

            # Verify time filter was applied
            call_args = mock_qdrant_client.search.call_args
            filters = call_args[1]['query_filter']
            assert filters is not None

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, conversation_memory, mock_qdrant_client, sample_memory_entries):
        """Test retrieving conversation history."""

        # Mock scroll results for conversation history
        mock_scroll_results = [
            Mock(id="mem1", payload={
                "content": sample_memory_entries[0].content,
                "timestamp": sample_memory_entries[0].timestamp.isoformat(),
                "persona_name": "Alice",
                "memory_type": "conversation",
                "metadata": sample_memory_entries[0].metadata
            }),
            Mock(id="mem3", payload={
                "content": sample_memory_entries[2].content,
                "timestamp": sample_memory_entries[2].timestamp.isoformat(),
                "persona_name": "Alice",
                "memory_type": "conversation",
                "metadata": sample_memory_entries[2].metadata
            })
        ]

        mock_qdrant_client.scroll.return_value = (mock_scroll_results, None)

        with patch.object(qdrant_client, 'scroll', new=mock_qdrant_client.scroll):

            history = await conversation_memory.get_conversation_history(
                persona_name="Alice",
                limit=50
            )

            assert len(history) == 2
            assert all(entry['memory_type'] == 'conversation' for entry in history)

            # Verify scroll was called with conversation filter
            call_args = mock_qdrant_client.scroll.call_args
            assert call_args[1]['collection_name'] == 'conversation_memory'
            assert call_args[1]['limit'] == 50

    @pytest.mark.asyncio
    async def test_clear_persona_memories(self, conversation_memory, mock_qdrant_client):
        """Test clearing all memories for a specific persona."""

        with patch.object(qdrant_client, 'delete', new=mock_qdrant_client.delete):

            result = await conversation_memory.clear_persona_memories("Alice")

            assert result is True
            mock_qdrant_client.delete.assert_called_once()

            # Verify delete was called with persona filter
            call_args = mock_qdrant_client.delete.call_args
            assert call_args[1]['collection_name'] == 'conversation_memory'
            filters = call_args[1]['points_selector']
            assert filters is not None

    @pytest.mark.asyncio
    async def test_clear_all_memories(self, conversation_memory, mock_qdrant_client):
        """Test clearing all memories from the collection."""

        with patch.object(qdrant_client, 'delete', new=mock_qdrant_client.delete):

            result = await conversation_memory.clear_all_memories()

            assert result is True
            mock_qdrant_client.delete.assert_called_once()

            # Verify entire collection was targeted
            call_args = mock_qdrant_client.delete.call_args
            assert call_args[1]['collection_name'] == 'conversation_memory'


class TestConversationMemoryMetadata:
    """Test memory operations with metadata."""

    @pytest.mark.asyncio
    async def test_store_memory_with_rich_metadata(self, conversation_memory, mock_qdrant_client):
        """Test storing memory with rich metadata."""

        rich_metadata = {
            "objects_involved": ["lamp_001", "desk"],
            "user_emotion": "satisfied",
            "action_success": True,
            "room_context": {
                "lighting": "dim",
                "time_of_day": "evening"
            }
        }

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            result = await conversation_memory.store_memory_from_text(
                content="User successfully turned on the lamp",
                persona_name="Alice",
                memory_type="action",
                metadata=rich_metadata
            )

            assert result is True

            # Verify metadata was preserved in the upsert call
            call_args = mock_qdrant_client.upsert.call_args
            point_payload = call_args[1]['points'][0].payload
            assert point_payload['metadata'] == rich_metadata

    @pytest.mark.asyncio
    async def test_search_by_metadata_fields(self, conversation_memory, mock_qdrant_client):
        """Test searching memories by specific metadata fields."""

        mock_qdrant_client.search.return_value = []

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            await conversation_memory.search_memories_by_metadata(
                metadata_filters={"objects_involved": "lamp_001"},
                persona_name="Alice",
                limit=10
            )

            # Verify metadata filter was applied
            call_args = mock_qdrant_client.search.call_args
            filters = call_args[1]['query_filter']
            assert filters is not None


class TestConversationMemoryErrorHandling:
    """Test error handling in memory operations."""

    @pytest.mark.asyncio
    async def test_handles_qdrant_connection_failure(self, conversation_memory, mock_qdrant_client):
        """Test graceful handling of Qdrant connection failures."""

        mock_qdrant_client.upsert.side_effect = Exception("Connection failed")

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert):

            result = await conversation_memory.store_memory_from_text(
                content="Test memory",
                persona_name="Alice",
                memory_type="conversation"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_handles_embedding_generation_failure(self, conversation_memory, mock_qdrant_client):
        """Test handling of embedding generation failures."""

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert), \
             patch('app.services.conversation_memory.generate_embedding', side_effect=Exception("Embedding failed")):

            result = await conversation_memory.store_memory_from_text(
                content="Test memory",
                persona_name="Alice",
                memory_type="conversation"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_handles_malformed_search_results(self, conversation_memory, mock_qdrant_client):
        """Test handling of malformed search results from Qdrant."""

        # Mock malformed search results
        mock_malformed_results = [
            Mock(id="mem1", score=0.9, payload={}),  # Missing required fields
            Mock(id="mem2", score=0.8),  # Missing payload entirely
            None,  # Null result
        ]

        mock_qdrant_client.search.return_value = mock_malformed_results

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            results = await conversation_memory.search_relevant_memories(
                query="test query",
                persona_name="Alice"
            )

            # Should handle malformed results gracefully
            assert isinstance(results, list)
            # Results might be empty or filtered, but shouldn't crash


class TestConversationMemoryPerformance:
    """Test performance aspects of memory operations."""

    @pytest.mark.asyncio
    async def test_batch_memory_storage(self, conversation_memory, mock_qdrant_client):
        """Test efficient batch storage of multiple memories."""

        memory_entries = [
            {
                "content": f"Test memory {i}",
                "persona_name": "Alice",
                "memory_type": "conversation",
                "metadata": {"batch_id": "test_batch"}
            }
            for i in range(10)
        ]

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            result = await conversation_memory.store_memories_batch(memory_entries)

            assert result is True

            # Should make fewer calls than individual storage
            assert mock_qdrant_client.upsert.call_count <= 2  # Batched calls

    @pytest.mark.asyncio
    async def test_memory_search_performance(self, conversation_memory, mock_qdrant_client):
        """Test search performance with large result sets."""

        import time

        # Mock large search results
        large_results = [
            Mock(id=f"mem{i}", score=0.5 + i * 0.01, payload={
                "content": f"Memory {i}",
                "timestamp": datetime.now().isoformat(),
                "persona_name": "Alice",
                "memory_type": "conversation",
                "metadata": {}
            })
            for i in range(100)
        ]

        mock_qdrant_client.search.return_value = large_results

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            start_time = time.time()
            results = await conversation_memory.search_relevant_memories(
                query="test query",
                persona_name="Alice",
                limit=50
            )
            execution_time = time.time() - start_time

            assert len(results) <= 50  # Should respect limit
            assert execution_time < 1.0  # Should process quickly


class TestConversationMemoryIntegration:
    """Test integration scenarios with other services."""

    @pytest.mark.asyncio
    async def test_memory_storage_from_brain_council(self, conversation_memory, mock_qdrant_client):
        """Test storing memories generated by Brain Council decisions."""

        brain_council_memory = {
            "content": "User requested lamp activation, assistant complied successfully",
            "persona_name": "Alice",
            "memory_type": "action_result",
            "metadata": {
                "user_intent": "lighting_control",
                "actions_taken": ["move", "interact"],
                "objects_affected": ["lamp_001"],
                "success": True,
                "user_satisfaction": "high"
            }
        }

        with patch.object(qdrant_client, 'upsert', new=mock_qdrant_client.upsert), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            result = await conversation_memory.store_brain_council_memory(brain_council_memory)

            assert result is True
            mock_qdrant_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_retrieval_for_context_building(self, conversation_memory, mock_qdrant_client, sample_memory_entries):
        """Test retrieving memories for Brain Council context building."""

        mock_search_results = [
            Mock(id="mem1", score=0.9, payload={
                "content": sample_memory_entries[0].content,
                "timestamp": sample_memory_entries[0].timestamp.isoformat(),
                "persona_name": "Alice",
                "memory_type": "conversation",
                "metadata": sample_memory_entries[0].metadata
            })
        ]

        mock_qdrant_client.search.return_value = mock_search_results

        with patch.object(qdrant_client, 'search', new=mock_qdrant_client.search), \
             patch('app.services.conversation_memory.generate_embedding', return_value=[0.1, 0.2, 0.3]):

            context = await conversation_memory.build_context_for_brain_council(
                current_query="Turn on the lamp",
                persona_name="Alice",
                recent_hours=24,
                max_memories=5
            )

            assert isinstance(context, list)
            assert len(context) > 0
            assert all("content" in memory for memory in context)
            assert all("relevance" in memory for memory in context)