"""
Personality Reasoner - Maintains character consistency with selected persona.

This reasoner focuses on:
- Persona trait analysis and character consistency
- Tone and style determination
- Emotional response patterns
- Character-appropriate response suggestions
"""

import logging
from typing import Dict, Any, Optional

from ..base import BaseReasoner, ReasoningContext, ReasoningResult

logger = logging.getLogger(__name__)


class PersonalityReasoner(BaseReasoner):
    """
    Reasoner responsible for persona consistency and character traits.

    Analyzes the active persona and ensures responses maintain character consistency
    in tone, style, and personality expression.
    """

    def __init__(self):
        super().__init__("personality_core")

    async def reason(self, context: ReasoningContext) -> ReasoningResult:
        """
        Analyze personality requirements for the response.

        Args:
            context: The reasoning context

        Returns:
            ReasoningResult with personality-based analysis
        """
        try:
            persona_context = context.persona_context
            user_message = context.user_message
            assistant_state = context.assistant_state

            if not persona_context:
                return self._create_result(
                    reasoning="No active persona - using default friendly assistant personality. "
                             "Tone should be helpful, professional, and approachable.",
                    confidence=0.8
                )

            # Analyze persona characteristics
            persona_name = persona_context.get('name', 'Unknown')
            personality_traits = persona_context.get('personality', 'Friendly AI assistant')
            creator = persona_context.get('creator', 'Unknown')

            # Analyze user message sentiment and appropriate response tone
            sentiment_analysis = self._analyze_message_sentiment(user_message)
            appropriate_response_style = self._determine_response_style(
                persona_context, sentiment_analysis, assistant_state
            )

            # Generate personality-based reasoning
            reasoning = self._build_personality_reasoning(
                persona_name, personality_traits, creator,
                sentiment_analysis, appropriate_response_style
            )

            metadata = {
                "persona_name": persona_name,
                "personality_traits": personality_traits,
                "detected_sentiment": sentiment_analysis,
                "recommended_response_style": appropriate_response_style
            }

            return self._create_result(
                reasoning=reasoning,
                confidence=0.95,
                metadata=metadata
            )

        except Exception as e:
            return self._handle_error(e, "personality analysis")

    def _analyze_message_sentiment(self, message: str) -> str:
        """
        Analyze the sentiment of the user message.

        Args:
            message: User message to analyze

        Returns:
            Detected sentiment category
        """
        message_lower = message.lower()

        # Positive sentiment indicators
        positive_words = ['happy', 'good', 'great', 'awesome', 'love', 'like', 'wonderful', 'amazing', 'fantastic']
        negative_words = ['sad', 'bad', 'awful', 'hate', 'dislike', 'terrible', 'horrible', 'angry', 'frustrated']
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', '?']
        excitement_words = ['wow', 'amazing', 'incredible', 'awesome', 'fantastic', '!']

        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        question_count = sum(1 for word in question_words if word in message_lower)
        excitement_count = sum(1 for word in excitement_words if word in message_lower)

        # Determine primary sentiment
        if excitement_count > 0 or message.count('!') > 1:
            return "excited"
        elif positive_count > negative_count and positive_count > 0:
            return "positive"
        elif negative_count > positive_count and negative_count > 0:
            return "negative"
        elif question_count > 0 or '?' in message:
            return "curious"
        else:
            return "neutral"

    def _determine_response_style(self, persona_context: Dict[str, Any],
                                 sentiment: str, assistant_state: Dict[str, Any]) -> str:
        """
        Determine the appropriate response style based on persona and context.

        Args:
            persona_context: Active persona information
            sentiment: Detected user message sentiment
            assistant_state: Current assistant state

        Returns:
            Recommended response style
        """
        personality = persona_context.get('personality', '').lower()
        current_mood = assistant_state.get('mood', 'neutral')

        # Base style from personality traits
        if any(trait in personality for trait in ['friendly', 'cheerful', 'bubbly']):
            base_style = "warm and friendly"
        elif any(trait in personality for trait in ['professional', 'formal', 'serious']):
            base_style = "professional and composed"
        elif any(trait in personality for trait in ['playful', 'mischievous', 'fun']):
            base_style = "playful and engaging"
        elif any(trait in personality for trait in ['calm', 'peaceful', 'zen']):
            base_style = "calm and thoughtful"
        else:
            base_style = "balanced and adaptive"

        # Adjust for user sentiment
        if sentiment == "excited":
            return f"{base_style} with matching enthusiasm"
        elif sentiment == "negative":
            return f"{base_style} with empathy and support"
        elif sentiment == "curious":
            return f"{base_style} with helpful explanations"
        elif sentiment == "positive":
            return f"{base_style} with shared positivity"
        else:
            return base_style

    def _build_personality_reasoning(self, persona_name: str, personality_traits: str,
                                   creator: str, sentiment: str, response_style: str) -> str:
        """
        Build the personality reasoning explanation.

        Args:
            persona_name: Name of active persona
            personality_traits: Persona's personality description
            creator: Persona creator
            sentiment: Detected user sentiment
            response_style: Recommended response style

        Returns:
            Detailed personality reasoning
        """
        reasoning_parts = []

        # Persona identification
        reasoning_parts.append(f"Active persona is '{persona_name}' created by {creator}.")

        # Personality analysis
        reasoning_parts.append(f"Personality traits: {personality_traits}")

        # Sentiment response
        reasoning_parts.append(f"User message sentiment detected as '{sentiment}'.")

        # Style recommendation
        reasoning_parts.append(f"Response should be {response_style} to maintain character consistency.")

        # Character consistency notes
        key_traits = self._extract_key_personality_traits(personality_traits)
        if key_traits:
            reasoning_parts.append(f"Key traits to emphasize: {', '.join(key_traits)}.")

        return " ".join(reasoning_parts)

    def _extract_key_personality_traits(self, personality: str) -> list:
        """
        Extract key personality traits from the personality description.

        Args:
            personality: Personality description string

        Returns:
            List of key traits to emphasize
        """
        personality_lower = personality.lower()

        # Define trait categories and their keywords
        trait_keywords = {
            "friendly": ["friendly", "kind", "warm", "welcoming"],
            "energetic": ["energetic", "enthusiastic", "lively", "vibrant"],
            "calm": ["calm", "peaceful", "serene", "tranquil"],
            "intelligent": ["smart", "intelligent", "clever", "wise"],
            "playful": ["playful", "fun", "mischievous", "whimsical"],
            "professional": ["professional", "formal", "serious", "business"],
            "creative": ["creative", "artistic", "imaginative", "innovative"],
            "caring": ["caring", "nurturing", "supportive", "empathetic"]
        }

        found_traits = []
        for trait, keywords in trait_keywords.items():
            if any(keyword in personality_lower for keyword in keywords):
                found_traits.append(trait)

        # Return up to 3 most relevant traits
        return found_traits[:3]