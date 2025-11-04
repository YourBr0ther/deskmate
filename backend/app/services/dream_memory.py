"""
Dream Memory Service - Manages autonomous action storage for idle mode.

Dreams are actions performed by the assistant while in idle mode. They are
stored in a separate Qdrant collection with expiration timestamps and can be
retrieved when the assistant returns to active mode.

Features:
- Store autonomous actions as dreams with vector embeddings
- Automatic expiration after configured hours
- Retrieve relevant dreams for context when switching modes
- Cleanup expired dreams automatically
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from app.config import config
from app.db.qdrant import qdrant_manager
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class DreamEntry:
    """Represents a single dream (autonomous action) in memory."""

    def __init__(
        self,
        action_type: str,
        content: str,
        action_data: Dict[str, Any],
        room_state: Dict[str, Any],
        assistant_position: Dict[str, int],
        success: bool = True,
        reasoning: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.action_type = action_type
        self.content = content
        self.action_data = action_data
        self.room_state = room_state
        self.assistant_position = assistant_position
        self.success = success
        self.reasoning = reasoning
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(hours=config.idle.dream_expiration_hours)

    def to_dict(self) -> Dict[str, Any]:
        """Convert dream to dictionary for storage and API responses."""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "content": self.content,
            "action_data": self.action_data,
            "room_state": self.room_state,
            "assistant_position": self.assistant_position,
            "success": self.success,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_dream": True
        }


class DreamMemoryService:
    """Service for managing dream (autonomous action) storage and retrieval."""

    def __init__(self):
        self.collection_name = "dreams"
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self):
        """Start background task to clean up expired dreams."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Started dream cleanup task")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped dream cleanup task")

    async def _cleanup_loop(self):
        """Background loop to periodically clean up expired dreams."""
        while True:
            try:
                await self.cleanup_expired_dreams()
                # Clean up every hour
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dream cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def store_dream(
        self,
        action_type: str,
        content: str,
        action_data: Dict[str, Any],
        room_state: Dict[str, Any],
        assistant_position: Dict[str, int],
        success: bool = True,
        reasoning: Optional[str] = None
    ) -> str:
        """
        Store a dream (autonomous action) in memory.

        Args:
            action_type: Type of action performed (move, interact, state_change, etc.)
            content: Natural language description of the action
            action_data: Structured data about the action
            room_state: Snapshot of room state when action occurred
            assistant_position: Assistant position when action occurred
            success: Whether the action was successful
            reasoning: AI reasoning behind the action

        Returns:
            Dream ID
        """
        try:
            dream = DreamEntry(
                action_type=action_type,
                content=content,
                action_data=action_data,
                room_state=room_state,
                assistant_position=assistant_position,
                success=success,
                reasoning=reasoning
            )

            # Generate embedding for the dream content
            embedding = await embedding_service.embed_text(content)

            # Store in Qdrant
            await qdrant_manager.add_memories(
                collection_name=self.collection_name,
                memories=[{
                    "id": dream.id,
                    "text": content,
                    "embedding": embedding,
                    "metadata": dream.to_dict()
                }]
            )

            logger.info(f"Stored dream: {action_type} - {content[:50]}...")
            return dream.id

        except Exception as e:
            logger.error(f"Failed to store dream: {e}")
            raise

    async def get_recent_dreams(
        self,
        limit: int = 10,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent dreams within specified time window.

        Args:
            limit: Maximum number of dreams to return
            hours_back: How many hours back to search

        Returns:
            List of dream dictionaries
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            results = await qdrant_manager.search_memories(
                collection_name=self.collection_name,
                query_text="",  # Empty query to get all
                limit=limit,
                filter_dict={
                    "created_at": {
                        "gte": cutoff_time.isoformat()
                    }
                }
            )

            dreams = []
            for result in results:
                if "metadata" in result:
                    dreams.append(result["metadata"])

            # Sort by creation time (most recent first)
            dreams.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            return dreams

        except Exception as e:
            logger.error(f"Failed to get recent dreams: {e}")
            return []

    async def search_relevant_dreams(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for dreams relevant to a query.

        Args:
            query: Search query text
            limit: Maximum number of results
            min_score: Minimum similarity score

        Returns:
            List of relevant dream dictionaries with scores
        """
        try:
            results = await qdrant_manager.search_memories(
                collection_name=self.collection_name,
                query_text=query,
                limit=limit
            )

            relevant_dreams = []
            for result in results:
                if result.get("score", 0) >= min_score and "metadata" in result:
                    dream_data = result["metadata"].copy()
                    dream_data["relevance_score"] = result["score"]
                    relevant_dreams.append(dream_data)

            return relevant_dreams

        except Exception as e:
            logger.error(f"Failed to search dreams: {e}")
            return []

    async def get_dream_by_id(self, dream_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific dream by ID."""
        try:
            result = await qdrant_manager.get_memory_by_id(
                collection_name=self.collection_name,
                memory_id=dream_id
            )

            if result and "metadata" in result:
                return result["metadata"]

            return None

        except Exception as e:
            logger.error(f"Failed to get dream {dream_id}: {e}")
            return None

    async def cleanup_expired_dreams(self) -> int:
        """
        Remove expired dreams from storage.

        Returns:
            Number of dreams cleaned up
        """
        try:
            current_time = datetime.utcnow()

            # Get all dreams to check expiration
            all_dreams = await qdrant_manager.search_memories(
                collection_name=self.collection_name,
                query_text="",  # Get all
                limit=1000  # Reasonable limit for cleanup
            )

            expired_ids = []
            for result in all_dreams:
                if "metadata" in result:
                    expires_at_str = result["metadata"].get("expires_at")
                    if expires_at_str:
                        try:
                            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                            if expires_at < current_time:
                                expired_ids.append(result["metadata"]["id"])
                        except ValueError:
                            # Invalid date format, remove this entry
                            expired_ids.append(result["metadata"]["id"])

            # Delete expired dreams
            if expired_ids:
                await qdrant_manager.delete_memories(
                    collection_name=self.collection_name,
                    memory_ids=expired_ids
                )
                logger.info(f"Cleaned up {len(expired_ids)} expired dreams")

            return len(expired_ids)

        except Exception as e:
            logger.error(f"Failed to cleanup expired dreams: {e}")
            return 0

    async def get_dream_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored dreams."""
        try:
            # Get recent dreams for analysis
            recent_dreams = await self.get_recent_dreams(limit=100, hours_back=24)

            total_count = len(recent_dreams)
            success_count = sum(1 for d in recent_dreams if d.get("success", True))

            action_types = {}
            for dream in recent_dreams:
                action_type = dream.get("action_type", "unknown")
                action_types[action_type] = action_types.get(action_type, 0) + 1

            return {
                "total_dreams_24h": total_count,
                "successful_actions": success_count,
                "failed_actions": total_count - success_count,
                "success_rate": success_count / total_count if total_count > 0 else 0,
                "action_types": action_types,
                "last_dream": recent_dreams[0] if recent_dreams else None
            }

        except Exception as e:
            logger.error(f"Failed to get dream statistics: {e}")
            return {
                "total_dreams_24h": 0,
                "successful_actions": 0,
                "failed_actions": 0,
                "success_rate": 0,
                "action_types": {},
                "last_dream": None
            }


# Global dream memory service instance
dream_memory = DreamMemoryService()