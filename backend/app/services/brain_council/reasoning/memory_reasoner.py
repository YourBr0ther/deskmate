"""
Memory Reasoner - Retrieves relevant context from past interactions.

This reasoner focuses on:
- Retrieving relevant conversation history
- Identifying patterns and preferences from past interactions
- Providing context about previous discussions
- Analyzing conversation continuity and themes
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..base import BaseReasoner, ReasoningContext, ReasoningResult
from app.services.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)


class MemoryReasoner(BaseReasoner):
    """
    Reasoner responsible for context retrieval and memory integration.

    Analyzes conversation history and retrieves relevant past interactions
    to inform the current response with appropriate context.
    """

    def __init__(self):
        super().__init__("memory_keeper")

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Analyze memory and provide relevant context for the response.

        Args:
            context: The reasoning context

        Returns:
            ReasoningResult with memory-based analysis
        """
        try:
            user_message = context.user_message
            persona_context = context.persona_context
            conversation_context = context.conversation_context

            # Analyze current conversation context
            memory_analysis = await self._analyze_conversation_context(
                conversation_context, user_message, persona_context
            )

            # Identify patterns and preferences
            patterns = self._identify_conversation_patterns(conversation_context)

            # Generate memory-based reasoning
            reasoning = self._build_memory_reasoning(
                memory_analysis, patterns, user_message, persona_context
            )

            metadata = {
                "conversation_length": len(conversation_context) if conversation_context else 0,
                "relevant_memories_count": memory_analysis.get("relevant_count", 0),
                "identified_patterns": patterns,
                "memory_coverage": memory_analysis.get("coverage", "none")
            }

            return self._create_result(
                reasoning=reasoning,
                confidence=0.9 if conversation_context else 0.5,
                metadata=metadata
            )

        except Exception as e:
            return self._handle_error(e, "memory analysis")

    async def _analyze_conversation_context(self, conversation_context: Optional[List[Any]],
                                          current_message: str,
                                          persona_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the conversation context for relevant information.

        Args:
            conversation_context: List of conversation messages
            current_message: Current user message
            persona_context: Active persona information

        Returns:
            Analysis of conversation context
        """
        if not conversation_context:
            return {
                "relevant_count": 0,
                "coverage": "none",
                "recent_topics": [],
                "user_preferences": {},
                "conversation_continuity": "new_conversation"
            }

        try:
            # Separate recent from retrieved memories
            recent_size = getattr(conversation_memory, 'recent_context_size', 20)
            recent_messages = conversation_context[-recent_size:] if len(conversation_context) > recent_size else conversation_context
            retrieved_messages = conversation_context[:-recent_size] if len(conversation_context) > recent_size else []

            # Analyze recent conversation
            recent_topics = self._extract_recent_topics(recent_messages)
            user_preferences = self._extract_user_preferences(conversation_context)
            conversation_continuity = self._analyze_continuity(recent_messages, current_message)

            # Check relevance of retrieved memories
            relevant_retrieved_count = len(retrieved_messages)

            return {
                "relevant_count": relevant_retrieved_count,
                "coverage": "full" if relevant_retrieved_count > 0 else "recent_only",
                "recent_topics": recent_topics,
                "user_preferences": user_preferences,
                "conversation_continuity": conversation_continuity,
                "recent_messages_count": len(recent_messages),
                "retrieved_messages_count": relevant_retrieved_count
            }

        except Exception as e:
            logger.warning(f"Error analyzing conversation context: {e}")
            return {
                "relevant_count": 0,
                "coverage": "error",
                "recent_topics": [],
                "user_preferences": {},
                "conversation_continuity": "unknown"
            }

    def _extract_recent_topics(self, messages: List[Any]) -> List[str]:
        """
        Extract main topics from recent conversation.

        Args:
            messages: List of recent conversation messages

        Returns:
            List of identified topics
        """
        try:
            topics = set()

            # Topic keywords and categories
            topic_keywords = {
                "movement": ["move", "go", "walk", "travel", "position"],
                "objects": ["pick", "grab", "take", "put", "place", "object"],
                "room": ["room", "space", "environment", "around", "here"],
                "feelings": ["feel", "mood", "happy", "sad", "excited", "calm"],
                "preferences": ["like", "love", "prefer", "favorite", "enjoy"],
                "questions": ["what", "how", "why", "when", "where", "tell me"],
                "greetings": ["hello", "hi", "hey", "good morning", "good evening"],
                "tasks": ["do", "help", "can you", "please", "task", "work"]
            }

            for message in messages[-10:]:  # Check last 10 messages
                if hasattr(message, 'content'):
                    content = message.content.lower()
                    for topic, keywords in topic_keywords.items():
                        if any(keyword in content for keyword in keywords):
                            topics.add(topic)

            return list(topics)[:5]  # Return up to 5 most recent topics

        except Exception as e:
            logger.warning(f"Error extracting topics: {e}")
            return []

    def _extract_user_preferences(self, messages: List[Any]) -> Dict[str, Any]:
        """
        Extract user preferences from conversation history.

        Args:
            messages: List of all conversation messages

        Returns:
            Dictionary of detected user preferences
        """
        try:
            preferences = {
                "communication_style": "unknown",
                "activity_preferences": [],
                "mentioned_interests": [],
                "interaction_frequency": "normal"
            }

            user_messages = [msg for msg in messages if hasattr(msg, 'role') and msg.role == 'user']

            if not user_messages:
                return preferences

            # Analyze communication style
            total_length = sum(len(msg.content) for msg in user_messages)
            avg_length = total_length / len(user_messages)

            if avg_length > 100:
                preferences["communication_style"] = "detailed"
            elif avg_length < 30:
                preferences["communication_style"] = "concise"
            else:
                preferences["communication_style"] = "balanced"

            # Look for activity preferences
            activity_keywords = {
                "exploration": ["explore", "look around", "see", "discover"],
                "interaction": ["talk", "chat", "conversation", "discuss"],
                "tasks": ["help", "do", "work", "task", "accomplish"],
                "learning": ["learn", "understand", "explain", "teach"]
            }

            for message in user_messages:
                content = message.content.lower()
                for activity, keywords in activity_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        preferences["activity_preferences"].append(activity)

            # Remove duplicates
            preferences["activity_preferences"] = list(set(preferences["activity_preferences"]))

            return preferences

        except Exception as e:
            logger.warning(f"Error extracting preferences: {e}")
            return {"communication_style": "unknown", "activity_preferences": [], "mentioned_interests": []}

    def _analyze_continuity(self, recent_messages: List[Any], current_message: str) -> str:
        """
        Analyze conversation continuity with current message.

        Args:
            recent_messages: Recent conversation messages
            current_message: Current user message

        Returns:
            Continuity assessment
        """
        try:
            if not recent_messages:
                return "new_conversation"

            # Get last few messages
            last_messages = recent_messages[-3:]
            last_content = " ".join(msg.content.lower() for msg in last_messages if hasattr(msg, 'content'))
            current_lower = current_message.lower()

            # Check for topic continuity
            continuity_indicators = {
                "direct_continuation": ["also", "and", "but", "however", "additionally"],
                "question_followup": ["what about", "how about", "can you also", "what if"],
                "topic_shift": ["now", "next", "let's", "change topic", "different"],
                "clarification": ["what do you mean", "explain", "I don't understand", "clarify"]
            }

            for continuity_type, indicators in continuity_indicators.items():
                if any(indicator in current_lower for indicator in indicators):
                    return continuity_type

            # Check for keyword overlap
            last_words = set(last_content.split())
            current_words = set(current_lower.split())
            overlap = len(last_words.intersection(current_words))

            if overlap > 3:
                return "topic_continuation"
            elif overlap > 1:
                return "related_topic"
            else:
                return "topic_shift"

        except Exception as e:
            logger.warning(f"Error analyzing continuity: {e}")
            return "unknown"

    def _identify_conversation_patterns(self, conversation_context: Optional[List[Any]]) -> List[str]:
        """
        Identify patterns in the conversation.

        Args:
            conversation_context: Full conversation context

        Returns:
            List of identified patterns
        """
        if not conversation_context:
            return []

        try:
            patterns = []

            # Check for recurring themes
            user_messages = [msg.content.lower() for msg in conversation_context
                           if hasattr(msg, 'role') and msg.role == 'user']

            if len(user_messages) >= 3:
                # Check for question patterns
                question_count = sum(1 for msg in user_messages if '?' in msg)
                if question_count > len(user_messages) * 0.6:
                    patterns.append("inquiry_focused")

                # Check for action patterns
                action_words = ['do', 'go', 'move', 'pick', 'take', 'help']
                action_count = sum(1 for msg in user_messages
                                 if any(word in msg for word in action_words))
                if action_count > len(user_messages) * 0.5:
                    patterns.append("action_oriented")

                # Check for social patterns
                social_words = ['how are you', 'thank you', 'please', 'sorry']
                social_count = sum(1 for msg in user_messages
                                 if any(word in msg for word in social_words))
                if social_count > len(user_messages) * 0.3:
                    patterns.append("socially_engaging")

            return patterns[:3]  # Return up to 3 patterns

        except Exception as e:
            logger.warning(f"Error identifying patterns: {e}")
            return []

    def _build_memory_reasoning(self, memory_analysis: Dict[str, Any],
                              patterns: List[str], current_message: str,
                              persona_context: Optional[Dict[str, Any]]) -> str:
        """
        Build the memory reasoning explanation.

        Args:
            memory_analysis: Results from memory analysis
            patterns: Identified conversation patterns
            current_message: Current user message
            persona_context: Active persona information

        Returns:
            Detailed memory reasoning
        """
        reasoning_parts = []

        # Memory coverage assessment
        coverage = memory_analysis.get("coverage", "none")
        relevant_count = memory_analysis.get("relevant_count", 0)

        if coverage == "full":
            reasoning_parts.append(f"Rich conversation history available with {relevant_count} relevant past interactions.")
        elif coverage == "recent_only":
            reasoning_parts.append("Recent conversation context available, but no older relevant memories found.")
        else:
            reasoning_parts.append("Limited conversation history - treating as new interaction.")

        # Recent topics
        recent_topics = memory_analysis.get("recent_topics", [])
        if recent_topics:
            reasoning_parts.append(f"Recent conversation has covered: {', '.join(recent_topics)}.")

        # User preferences
        preferences = memory_analysis.get("user_preferences", {})
        if preferences.get("communication_style") != "unknown":
            reasoning_parts.append(f"User shows {preferences['communication_style']} communication style.")

        activity_prefs = preferences.get("activity_preferences", [])
        if activity_prefs:
            reasoning_parts.append(f"User appears interested in: {', '.join(activity_prefs)}.")

        # Conversation continuity
        continuity = memory_analysis.get("conversation_continuity", "unknown")
        if continuity != "unknown":
            if continuity == "direct_continuation":
                reasoning_parts.append("Message appears to continue the previous topic directly.")
            elif continuity == "topic_shift":
                reasoning_parts.append("Message introduces a new topic or direction.")
            elif continuity in ["related_topic", "topic_continuation"]:
                reasoning_parts.append("Message builds on recent conversation themes.")

        # Conversation patterns
        if patterns:
            reasoning_parts.append(f"Identified conversation patterns: {', '.join(patterns)}.")

        # Recommendations based on memory
        if memory_analysis.get("recent_messages_count", 0) > 5:
            reasoning_parts.append("Consider referencing recent interactions to maintain conversational flow.")

        if not reasoning_parts:
            reasoning_parts.append("No significant memory context to inform response. Focus on immediate user request.")

        return " ".join(reasoning_parts)