"""
Conversation Memory Service - SillyTavern-inspired memory management.

This service implements sophisticated conversation memory management using:
1. Short-term context window (recent messages)
2. Long-term vector-based memory (semantic retrieval)
3. Hybrid approach for optimal context inclusion
4. Automatic conversation summarization

Based on SillyTavern's Smart Context and Chat Vectorization approaches.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio

from app.db.qdrant import qdrant_manager
from app.services.llm_manager import llm_manager, ChatMessage
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Enhanced message structure for conversation memory."""
    id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    persona_name: Optional[str] = None
    embedding: Optional[List[float]] = None
    importance_score: float = 1.0  # 0.0-1.0, higher = more important
    message_type: str = "chat"  # "chat", "action", "system", "summary"
    metadata: Optional[Dict[str, Any]] = None

    def to_chat_message(self) -> ChatMessage:
        """Convert to basic ChatMessage for LLM."""
        return ChatMessage(
            role=self.role,
            content=self.content,
            timestamp=self.timestamp.isoformat()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ConversationMemoryService:
    """
    Manages conversation memory using SillyTavern-inspired approaches.

    Features:
    - Maintains recent context window (configurable size)
    - Stores ALL messages in vector database for semantic retrieval
    - Retrieves relevant past messages based on current conversation
    - Automatic importance scoring and summarization
    - Persona-aware conversation management
    """

    def __init__(self):
        self.recent_context_size = 20  # Number of recent messages to keep in context
        self.max_retrieved_memories = 5  # Max old messages to retrieve from vector DB
        self.conversation_id = None  # Current conversation session
        self.recent_messages: List[ConversationMessage] = []
        self.min_messages_for_vectorization = 2  # Start vectorizing after this many messages

    async def initialize_conversation(self, persona_name: Optional[str] = None, load_history: bool = True) -> str:
        """Start a new conversation session, optionally loading previous history."""
        self.conversation_id = str(uuid.uuid4())
        self.recent_messages = []

        if persona_name and load_history:
            # Load recent conversation history for this persona
            await self._load_persona_history(persona_name)

        if persona_name and not self.recent_messages:
            # Add system message about active persona if no history loaded
            system_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                role="system",
                content=f"Conversation started with persona: {persona_name}",
                timestamp=datetime.now(),
                persona_name=persona_name,
                message_type="system",
                importance_score=0.8
            )
            await self.add_message(system_msg)

        logger.info(f"Initialized conversation: {self.conversation_id} (persona: {persona_name}, messages loaded: {len(self.recent_messages)})")
        return self.conversation_id

    async def add_message(
        self,
        message: ConversationMessage
    ) -> bool:
        """
        Add a new message to conversation memory.

        Process:
        1. Add to recent context
        2. Generate embedding if needed
        3. Store in vector database
        4. Maintain context window size
        """
        try:
            # Ensure message has an ID
            if not message.id:
                message.id = str(uuid.uuid4())

            # Add to recent context
            self.recent_messages.append(message)

            # Generate embedding for non-system messages
            if message.role != "system" and message.content.strip():
                try:
                    embedding = await self._generate_embedding(message.content)
                    message.embedding = embedding
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for message: {e}")

            # Store in vector database if we have enough messages
            if len(self.recent_messages) >= self.min_messages_for_vectorization:
                await self._store_in_vector_db(message)

            # Maintain context window size
            if len(self.recent_messages) > self.recent_context_size:
                # Remove oldest message from recent context (but it stays in vector DB)
                removed = self.recent_messages.pop(0)
                logger.debug(f"Removed message from recent context: {removed.id}")

            logger.debug(f"Added message to conversation: {message.role} - {message.content[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to add message to conversation memory: {e}")
            return False

    async def get_conversation_context(
        self,
        current_message: str,
        persona_name: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Get optimal conversation context for LLM.

        Combines:
        1. Recent messages (always included)
        2. Relevant past messages (retrieved via vector search)

        Returns messages formatted for LLM consumption.
        """
        try:
            context_messages = []

            # Get relevant past messages via vector search
            if len(self.recent_messages) >= self.min_messages_for_vectorization:
                relevant_memories = await self._retrieve_relevant_memories(
                    current_message, persona_name
                )

                if relevant_memories:
                    logger.info(f"Retrieved {len(relevant_memories)} relevant memories")
                    context_messages.extend(relevant_memories)

            # Add recent messages (always include these)
            recent_chat_messages = [msg.to_chat_message() for msg in self.recent_messages]
            context_messages.extend(recent_chat_messages)

            # Remove duplicates while preserving order
            seen_ids = set()
            unique_messages = []
            for msg in context_messages:
                # Create a simple ID based on content and timestamp for deduplication
                msg_id = f"{msg.role}:{msg.content[:50]}:{msg.timestamp}"
                if msg_id not in seen_ids:
                    seen_ids.add(msg_id)
                    unique_messages.append(msg)

            logger.info(f"Prepared context with {len(unique_messages)} messages "
                       f"({len(recent_chat_messages)} recent, "
                       f"{len(context_messages) - len(recent_chat_messages)} retrieved)")

            return unique_messages

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            # Fallback to just recent messages
            return [msg.to_chat_message() for msg in self.recent_messages]

    async def add_user_message(
        self,
        content: str,
        persona_name: Optional[str] = None
    ) -> ConversationMessage:
        """Add a user message to the conversation."""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=content,
            timestamp=datetime.now(),
            persona_name=persona_name,
            importance_score=self._calculate_importance_score(content, "user"),
            message_type="chat"
        )

        await self.add_message(message)
        return message

    async def add_assistant_message(
        self,
        content: str,
        persona_name: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationMessage:
        """Add an assistant message to the conversation."""
        metadata = {}
        if actions:
            metadata["actions"] = actions

        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=content,
            timestamp=datetime.now(),
            persona_name=persona_name,
            importance_score=self._calculate_importance_score(content, "assistant"),
            message_type="chat",
            metadata=metadata
        )

        await self.add_message(message)
        return message

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using embedding service."""
        return await embedding_service.generate_embedding(text)

    async def _store_in_vector_db(self, message: ConversationMessage) -> bool:
        """Store message in vector database."""
        try:
            if not message.embedding:
                return False

            payload = {
                "conversation_id": self.conversation_id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "persona_name": message.persona_name,
                "importance_score": message.importance_score,
                "message_type": message.message_type,
                "metadata": message.metadata or {}
            }

            success = await qdrant_manager.insert_memory(
                collection="memories",
                memory_id=message.id,
                vector=message.embedding,
                payload=payload
            )

            if success:
                logger.debug(f"Stored message in vector DB: {message.id}")

            return success

        except Exception as e:
            logger.error(f"Failed to store message in vector DB: {e}")
            return False

    async def _retrieve_relevant_memories(
        self,
        current_message: str,
        persona_name: Optional[str] = None
    ) -> List[ChatMessage]:
        """Retrieve relevant past messages using vector search."""
        try:
            # Generate embedding for current message
            query_embedding = await self._generate_embedding(current_message)

            # Search for relevant memories
            results = await qdrant_manager.search_memories(
                collection="memories",
                query_vector=query_embedding,
                limit=self.max_retrieved_memories,
                score_threshold=0.7  # Only include fairly relevant matches
            )

            # Convert results to ChatMessage objects
            relevant_messages = []
            for result in results:
                payload = result["payload"]

                # Filter by persona if specified
                if persona_name and payload.get("persona_name") != persona_name:
                    continue

                # Skip very recent messages (they're already in recent_messages)
                msg_time = datetime.fromisoformat(payload["timestamp"])
                if datetime.now() - msg_time < timedelta(minutes=5):
                    continue

                chat_msg = ChatMessage(
                    role=payload["role"],
                    content=payload["content"],
                    timestamp=payload["timestamp"]
                )
                relevant_messages.append(chat_msg)

            return relevant_messages

        except Exception as e:
            logger.error(f"Failed to retrieve relevant memories: {e}")
            return []

    def _calculate_importance_score(self, content: str, role: str) -> float:
        """Calculate importance score for a message (0.0-1.0)."""
        try:
            score = 0.5  # Base score

            # Role-based scoring
            if role == "user":
                score += 0.1  # User messages are slightly more important
            elif role == "system":
                score += 0.3  # System messages are quite important

            # Content-based scoring
            content_lower = content.lower()

            # Important keywords boost score
            important_keywords = [
                "remember", "important", "never forget", "always",
                "name is", "i am", "my name", "call me",
                "favorite", "love", "hate", "afraid",
                "birthday", "anniversary", "special"
            ]

            for keyword in important_keywords:
                if keyword in content_lower:
                    score += 0.2

            # Length-based scoring (longer messages often more important)
            if len(content) > 100:
                score += 0.1
            if len(content) > 300:
                score += 0.1

            # Clamp to valid range
            return min(1.0, max(0.0, score))

        except Exception:
            return 0.5  # Default score

    async def get_conversation_summary(self) -> str:
        """Generate a summary of the current conversation."""
        try:
            if len(self.recent_messages) < 5:
                return "Conversation just started."

            # Get key messages for summary
            important_messages = [
                msg for msg in self.recent_messages
                if msg.importance_score > 0.7 and msg.role != "system"
            ]

            if not important_messages:
                important_messages = self.recent_messages[-5:]  # Last 5 messages

            # Format for summarization
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in important_messages
            ])

            # Generate summary using LLM
            summary_prompt = f"""Summarize this conversation in 2-3 sentences, focusing on key topics and character details:

{conversation_text}

Summary:"""

            messages = [ChatMessage(role="user", content=summary_prompt)]

            response = ""
            async for chunk in llm_manager.chat_completion_stream(messages=messages, temperature=0.3):
                if chunk:
                    response += chunk

            return response.strip() or "Unable to generate summary."

        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            return "Unable to generate summary."

    async def _load_persona_history(self, persona_name: str) -> None:
        """Load recent conversation history for a specific persona."""
        try:
            # Search for recent messages with this persona
            results = await qdrant_manager.search_memories(
                collection="memories",
                query_vector=[0.1] * 1536,  # Dummy query vector for now
                limit=50,  # Get more to filter by persona and recency
                score_threshold=0.0  # Accept all matches for history loading
            )

            # Filter and sort by persona and timestamp
            persona_messages = []
            for result in results:
                payload = result["payload"]
                if payload.get("persona_name") == persona_name:
                    # Skip system messages for history loading
                    if payload.get("message_type") != "system":
                        try:
                            msg = ConversationMessage(
                                id=result["id"],
                                role=payload["role"],
                                content=payload["content"],
                                timestamp=datetime.fromisoformat(payload["timestamp"]),
                                persona_name=payload.get("persona_name"),
                                importance_score=payload.get("importance_score", 1.0),
                                message_type=payload.get("message_type", "chat"),
                                metadata=payload.get("metadata")
                            )
                            persona_messages.append(msg)
                        except Exception as e:
                            logger.warning(f"Failed to parse message from vector DB: {e}")

            # Sort by timestamp and take the most recent messages
            persona_messages.sort(key=lambda x: x.timestamp)
            recent_history = persona_messages[-self.recent_context_size:]

            # Add to recent messages
            self.recent_messages.extend(recent_history)

            logger.info(f"Loaded {len(recent_history)} messages from history for persona: {persona_name}")

        except Exception as e:
            logger.warning(f"Failed to load persona history for {persona_name}: {e}")

    async def get_chat_history_for_frontend(self, limit: int = 50, persona_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get formatted chat history for frontend display."""
        try:
            # Get recent messages plus some from vector DB
            all_messages = []

            # Add recent messages (filter by persona if specified)
            for msg in self.recent_messages:
                if (msg.role in ["user", "assistant"] and  # Skip system messages for frontend
                    (persona_name is None or msg.persona_name == persona_name)):  # Filter by persona
                    all_messages.append({
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "model": "current"  # Could be enhanced to track actual model
                    })

            # If we need more messages, get from vector DB
            if len(all_messages) < limit:
                # Search for more messages from this conversation
                results = await qdrant_manager.search_memories(
                    collection="memories",
                    query_vector=[0.1] * 1536,  # Dummy query for recent messages
                    limit=limit * 2,  # Get extra to filter
                    score_threshold=0.0
                )

                for result in results:
                    payload = result["payload"]
                    if (payload["role"] in ["user", "assistant"] and
                        payload.get("message_type", "chat") == "chat" and
                        (persona_name is None or payload.get("persona_name") == persona_name)):  # Filter by persona

                        # Check if we already have this message
                        existing_ids = {msg["id"] for msg in all_messages}
                        if result["id"] not in existing_ids:
                            all_messages.append({
                                "id": result["id"],
                                "role": payload["role"],
                                "content": payload["content"],
                                "timestamp": payload["timestamp"],
                                "model": "stored"
                            })

            # Sort by timestamp and limit
            all_messages.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))
            return all_messages[-limit:] if len(all_messages) > limit else all_messages

        except Exception as e:
            logger.error(f"Failed to get chat history for frontend: {e}")
            # Fallback to just recent messages
            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "model": "current"
                }
                for msg in self.recent_messages
                if msg.role in ["user", "assistant"]
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation memory statistics."""
        return {
            "conversation_id": self.conversation_id,
            "recent_messages_count": len(self.recent_messages),
            "recent_context_size": self.recent_context_size,
            "max_retrieved_memories": self.max_retrieved_memories,
            "vectorization_enabled": len(self.recent_messages) >= self.min_messages_for_vectorization,
            "average_importance_score": sum(msg.importance_score for msg in self.recent_messages) / len(self.recent_messages) if self.recent_messages else 0
        }

    async def clear_current_conversation(self) -> bool:
        """Clear only the current conversation (recent messages)."""
        try:
            self.recent_messages = []
            logger.info("Cleared current conversation messages")
            return True
        except Exception as e:
            logger.error(f"Failed to clear current conversation: {e}")
            return False

    async def clear_all_memory(self) -> bool:
        """Clear all conversation memory (current + vector database)."""
        try:
            # Clear current conversation
            await self.clear_current_conversation()

            # Clear vector database
            success = await qdrant_manager.clear_all_collections()

            if success:
                logger.info("Cleared all conversation memory")
            else:
                logger.error("Failed to clear vector database")

            return success
        except Exception as e:
            logger.error(f"Failed to clear all memory: {e}")
            return False

    async def clear_persona_memory(self, persona_name: str) -> bool:
        """Clear memory for a specific persona."""
        try:
            # Clear current conversation if it's for this persona
            current_persona_messages = [
                msg for msg in self.recent_messages
                if msg.persona_name != persona_name
            ]
            self.recent_messages = current_persona_messages

            # Clear from vector database
            success = await qdrant_manager.delete_persona_memories(persona_name)

            if success:
                logger.info(f"Cleared memory for persona: {persona_name}")
            else:
                logger.error(f"Failed to clear vector memory for persona: {persona_name}")

            return success
        except Exception as e:
            logger.error(f"Failed to clear persona memory: {e}")
            return False


# Global instance
conversation_memory = ConversationMemoryService()