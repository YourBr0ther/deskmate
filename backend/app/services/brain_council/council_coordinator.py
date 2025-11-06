"""
Council Coordinator - Orchestrates the Brain Council reasoning process.

This coordinator:
- Manages the execution of all five reasoners
- Coordinates parallel/sequential reasoning as needed
- Integrates reasoning results into final decisions
- Handles errors and fallback scenarios
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import (
    ReasoningContext, ReasoningResult, CouncilDecision,
    ReasonerFactory, BaseReasoner
)
from .reasoning import (
    PersonalityReasoner, MemoryReasoner, SpatialReasoner,
    ActionReasoner, ValidationReasoner
)
# Lazy import to avoid database issues

logger = logging.getLogger(__name__)


class CouncilCoordinator:
    """
    Coordinates the Brain Council reasoning process.

    Manages the execution of all reasoners and integrates their results
    into comprehensive decisions for the virtual AI companion.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_reasoners()

    def _initialize_reasoners(self):
        """Initialize and register all reasoner instances."""
        try:
            # Create reasoner instances
            personality_reasoner = PersonalityReasoner()
            memory_reasoner = MemoryReasoner()
            spatial_reasoner = SpatialReasoner()
            action_reasoner = ActionReasoner()
            validation_reasoner = ValidationReasoner()

            # Register with factory
            ReasonerFactory.register_reasoner("personality_core", personality_reasoner)
            ReasonerFactory.register_reasoner("memory_keeper", memory_reasoner)
            ReasonerFactory.register_reasoner("spatial_reasoner", spatial_reasoner)
            ReasonerFactory.register_reasoner("action_planner", action_reasoner)
            ReasonerFactory.register_reasoner("validator", validation_reasoner)

            self.logger.info("All Brain Council reasoners initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize reasoners: {e}")
            raise

    async def process_user_message(
        self,
        user_message: str,
        assistant_state: Dict[str, Any],
        room_state: Dict[str, Any],
        persona_context: Optional[Dict[str, Any]] = None
    ) -> CouncilDecision:
        """
        Process a user message through the complete Brain Council.

        Args:
            user_message: User's message to process
            assistant_state: Current assistant state
            room_state: Current room state
            persona_context: Active persona information

        Returns:
            CouncilDecision with integrated reasoning and actions
        """
        try:
            self.logger.info(f"Processing user message through Brain Council: {user_message[:50]}...")

            # Prepare reasoning context
            context = await self._prepare_reasoning_context(
                user_message, assistant_state, room_state, persona_context
            )

            # Execute reasoning process
            reasoning_results = await self._execute_reasoning_process(context)

            # Integrate results into final decision
            decision = await self._integrate_reasoning_results(
                reasoning_results, context
            )

            self.logger.info("Brain Council processing completed successfully")
            return decision

        except Exception as e:
            self.logger.error(f"Error in Brain Council processing: {e}")
            return self._create_fallback_decision(user_message, str(e))

    async def _prepare_reasoning_context(
        self,
        user_message: str,
        assistant_state: Dict[str, Any],
        room_state: Dict[str, Any],
        persona_context: Optional[Dict[str, Any]]
    ) -> ReasoningContext:
        """
        Prepare the reasoning context with all necessary information.

        Args:
            user_message: User's message
            assistant_state: Current assistant state
            room_state: Current room state
            persona_context: Active persona information

        Returns:
            Complete reasoning context
        """
        try:
            # Get conversation context for memory reasoner
            conversation_context = None
            if persona_context:
                from app.services.conversation_memory import conversation_memory
                persona_name = persona_context.get("name")
                conversation_context = await conversation_memory.get_conversation_context(
                    current_message=user_message,
                    persona_name=persona_name
                )

            return ReasoningContext(
                user_message=user_message,
                assistant_state=assistant_state,
                room_state=room_state,
                persona_context=persona_context,
                conversation_context=conversation_context,
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.warning(f"Error preparing reasoning context: {e}")
            # Return minimal context for fallback
            return ReasoningContext(
                user_message=user_message,
                assistant_state=assistant_state,
                room_state=room_state,
                persona_context=persona_context,
                timestamp=datetime.now()
            )

    async def _execute_reasoning_process(self, context: ReasoningContext) -> Dict[str, ReasoningResult]:
        """
        Execute the reasoning process with all council members.

        Args:
            context: The reasoning context

        Returns:
            Dictionary of reasoning results by reasoner name
        """
        try:
            # Get all reasoners
            reasoners = ReasonerFactory.get_all_reasoners()
            if not reasoners:
                raise Exception("No reasoners available")

            # Execute reasoners in parallel for better performance
            self.logger.info("Executing Brain Council reasoners in parallel")

            reasoning_tasks = {
                name: reasoner.reason(context)
                for name, reasoner in reasoners.items()
            }

            # Wait for all reasoning tasks to complete
            completed_results = await asyncio.gather(
                *reasoning_tasks.values(),
                return_exceptions=True
            )

            # Map results back to reasoner names
            reasoning_results = {}
            for i, (name, _) in enumerate(reasoning_tasks.items()):
                result = completed_results[i]
                if isinstance(result, Exception):
                    self.logger.error(f"Error in {name} reasoner: {result}")
                    reasoning_results[name] = ReasoningResult(
                        reasoner_name=name,
                        reasoning=f"Error in reasoning: {str(result)}",
                        confidence=0.0,
                        error=str(result)
                    )
                else:
                    reasoning_results[name] = result

            self.logger.info(f"Completed reasoning with {len(reasoning_results)} reasoners")
            return reasoning_results

        except Exception as e:
            self.logger.error(f"Error executing reasoning process: {e}")
            # Return error results for all expected reasoners
            error_result = ReasoningResult(
                reasoner_name="error",
                reasoning=f"Reasoning process failed: {str(e)}",
                confidence=0.0,
                error=str(e)
            )
            return {
                "personality_core": error_result,
                "memory_keeper": error_result,
                "spatial_reasoner": error_result,
                "action_planner": error_result,
                "validator": error_result
            }

    async def _integrate_reasoning_results(
        self,
        reasoning_results: Dict[str, ReasoningResult],
        context: ReasoningContext
    ) -> CouncilDecision:
        """
        Integrate all reasoning results into a final council decision.

        Args:
            reasoning_results: Results from all reasoners
            context: Original reasoning context

        Returns:
            Integrated council decision
        """
        try:
            # Extract reasoning from each council member
            council_reasoning = {}
            total_confidence = 0.0
            valid_reasoners = 0

            for name, result in reasoning_results.items():
                if result.is_valid:
                    council_reasoning[name] = result.reasoning
                    total_confidence += result.confidence
                    valid_reasoners += 1
                else:
                    council_reasoning[name] = result.reasoning or f"Error in {name}"
                    self.logger.warning(f"Invalid reasoning from {name}: {result.error}")

            # Calculate overall confidence
            overall_confidence = total_confidence / max(valid_reasoners, 1)

            # Extract proposed actions from action reasoner
            actions = self._extract_proposed_actions(reasoning_results, context)

            # Determine appropriate mood based on personality and situation
            mood = self._determine_response_mood(reasoning_results, context)

            # Generate natural response based on all reasoning
            response = self._generate_natural_response(reasoning_results, context)

            # Create brief explanation of reasoning process
            reasoning_summary = self._create_reasoning_summary(reasoning_results)

            return CouncilDecision(
                response=response,
                actions=actions,
                mood=mood,
                reasoning=reasoning_summary,
                council_reasoning=council_reasoning,
                confidence=overall_confidence,
                metadata={
                    "valid_reasoners": valid_reasoners,
                    "total_reasoners": len(reasoning_results),
                    "context_timestamp": context.timestamp.isoformat(),
                    "processing_completed": datetime.now().isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Error integrating reasoning results: {e}")
            return self._create_fallback_decision(context.user_message, str(e))

    def _extract_proposed_actions(
        self,
        reasoning_results: Dict[str, ReasoningResult],
        context: ReasoningContext
    ) -> List[Dict[str, Any]]:
        """Extract and validate proposed actions from reasoning results."""
        try:
            actions = []

            # Get proposed actions from action reasoner
            action_result = reasoning_results.get("action_planner")
            if action_result and action_result.is_valid:
                action_metadata = action_result.metadata or {}
                proposed_actions_count = action_metadata.get("proposed_actions_count", 0)

                # For now, create simple actions based on detected intent
                # In a full implementation, this would extract actual action proposals
                intent_analysis = action_metadata.get("detected_intent", {})
                primary_intent = intent_analysis.get("primary_intent", "conversation")

                if primary_intent == "movement" and proposed_actions_count > 0:
                    # Add a simple movement action as example
                    actions.append({
                        "type": "expression",
                        "target": "thoughtful",
                        "parameters": {}
                    })

                elif primary_intent == "object_interaction" and proposed_actions_count > 0:
                    # Add an interaction expression
                    actions.append({
                        "type": "expression",
                        "target": "engaged",
                        "parameters": {}
                    })

                elif primary_intent == "exploration":
                    actions.append({
                        "type": "expression",
                        "target": "curious",
                        "parameters": {}
                    })

            # Validate actions with validator results
            validation_result = reasoning_results.get("validator")
            if validation_result and validation_result.is_valid:
                validation_metadata = validation_result.metadata or {}
                safety_issues = validation_metadata.get("safety_issues_found", 0)

                if safety_issues > 0:
                    # Replace risky actions with safe alternatives
                    actions = [
                        action for action in actions
                        if action.get("type") == "expression"
                    ]

            return actions[:3]  # Limit to 3 actions maximum

        except Exception as e:
            self.logger.warning(f"Error extracting proposed actions: {e}")
            return []

    def _determine_response_mood(
        self,
        reasoning_results: Dict[str, ReasoningResult],
        context: ReasoningContext
    ) -> str:
        """Determine appropriate mood for the response."""
        try:
            # Get personality guidance
            personality_result = reasoning_results.get("personality_core")
            if personality_result and personality_result.is_valid:
                personality_metadata = personality_result.metadata or {}
                detected_sentiment = personality_metadata.get("detected_sentiment", "neutral")

                # Map sentiment to mood
                sentiment_to_mood = {
                    "excited": "excited",
                    "positive": "happy",
                    "negative": "concerned",
                    "curious": "curious",
                    "neutral": "content"
                }

                return sentiment_to_mood.get(detected_sentiment, "content")

            # Fallback based on current assistant mood
            current_mood = context.assistant_state.get("mood", "neutral")
            if current_mood in ["happy", "excited", "content", "curious", "concerned"]:
                return current_mood

            return "content"

        except Exception:
            return "neutral"

    def _generate_natural_response(
        self,
        reasoning_results: Dict[str, ReasoningResult],
        context: ReasoningContext
    ) -> str:
        """Generate a natural response based on all reasoning."""
        try:
            # Get key insights from each reasoner
            personality_insight = ""
            memory_insight = ""
            spatial_insight = ""
            action_insight = ""

            personality_result = reasoning_results.get("personality_core")
            if personality_result and personality_result.is_valid:
                metadata = personality_result.metadata or {}
                recommended_style = metadata.get("recommended_response_style", "balanced")
                personality_insight = f"Responding in a {recommended_style} manner"

            memory_result = reasoning_results.get("memory_keeper")
            if memory_result and memory_result.is_valid:
                metadata = memory_result.metadata or {}
                conversation_length = metadata.get("conversation_length", 0)
                if conversation_length > 0:
                    memory_insight = "building on our conversation"

            spatial_result = reasoning_results.get("spatial_reasoner")
            if spatial_result and spatial_result.is_valid:
                metadata = spatial_result.metadata or {}
                visible_objects = metadata.get("visible_objects_count", 0)
                if visible_objects > 0:
                    spatial_insight = f"while observing the {visible_objects} objects around me"

            action_result = reasoning_results.get("action_planner")
            if action_result and action_result.is_valid:
                metadata = action_result.metadata or {}
                intent = metadata.get("detected_intent", {}).get("primary_intent", "")
                if intent:
                    action_insight = f"understanding your interest in {intent}"

            # Compose response based on available insights
            response_parts = ["I understand"]

            if action_insight:
                response_parts.append(action_insight)

            if memory_insight:
                response_parts.append(memory_insight)

            if spatial_insight:
                response_parts.append(spatial_insight)

            response = " ".join(response_parts) + "."

            # Add personality style if available
            if personality_insight and "balanced" not in personality_insight.lower():
                response += f" {personality_insight.capitalize()}."

            return response

        except Exception as e:
            self.logger.warning(f"Error generating natural response: {e}")
            return "I understand what you're asking. Let me help you with that."

    def _create_reasoning_summary(self, reasoning_results: Dict[str, ReasoningResult]) -> str:
        """Create a brief summary of the reasoning process."""
        try:
            valid_reasoners = [
                name for name, result in reasoning_results.items()
                if result.is_valid
            ]

            if len(valid_reasoners) == len(reasoning_results):
                return f"Complete Brain Council analysis with {len(valid_reasoners)} perspectives integrated"
            elif len(valid_reasoners) > 0:
                return f"Brain Council analysis with {len(valid_reasoners)}/{len(reasoning_results)} reasoners contributing successfully"
            else:
                return "Fallback reasoning used due to council processing issues"

        except Exception:
            return "Brain Council reasoning completed"

    def _create_fallback_decision(self, user_message: str, error_msg: str) -> CouncilDecision:
        """Create a fallback decision when the main process fails."""
        return CouncilDecision(
            response="I understand what you're asking, but I'm having some technical difficulties processing the full context right now. Let me help you as best I can.",
            actions=[{
                "type": "expression",
                "target": "apologetic",
                "parameters": {}
            }],
            mood="concerned",
            reasoning=f"Fallback decision due to processing error: {error_msg}",
            council_reasoning={
                "error": f"Council processing failed: {error_msg}",
                "fallback": "Using simplified reasoning for user response"
            },
            confidence=0.3,
            metadata={
                "fallback": True,
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
        )