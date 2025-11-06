"""
Response Parser - Handles structured response parsing for Brain Council.

This parser:
- Parses LLM responses into structured data
- Handles JSON extraction and validation
- Provides fallback parsing for malformed responses
- Validates response structure and content
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Union

from .base import CouncilDecision

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Parses and validates LLM responses for Brain Council operations.

    Handles JSON extraction, validation, and fallback parsing for
    responses that may not be perfectly formatted.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_council_response(self, raw_response: str) -> CouncilDecision:
        """
        Parse a raw LLM response into a structured CouncilDecision.

        Args:
            raw_response: Raw response text from LLM

        Returns:
            Parsed and validated CouncilDecision
        """
        try:
            self.logger.debug(f"Parsing council response: {raw_response[:200]}...")

            # Extract JSON from response
            json_data = self._extract_json_from_response(raw_response)

            if not json_data:
                self.logger.warning("No valid JSON found in response, using fallback parsing")
                return self._create_fallback_decision(raw_response)

            # Validate and parse the JSON structure
            parsed_decision = self._parse_json_structure(json_data, raw_response)

            self.logger.debug("Successfully parsed council response")
            return parsed_decision

        except Exception as e:
            self.logger.error(f"Error parsing council response: {e}")
            return self._create_error_decision(raw_response, str(e))

    def parse_reasoner_response(self, raw_response: str, reasoner_name: str) -> Dict[str, Any]:
        """
        Parse a response from an individual reasoner.

        Args:
            raw_response: Raw response text from reasoner
            reasoner_name: Name of the reasoner that generated the response

        Returns:
            Parsed reasoner response data
        """
        try:
            # For individual reasoners, we expect simpler text responses
            cleaned_response = self._clean_response_text(raw_response)

            return {
                "reasoner_name": reasoner_name,
                "reasoning": cleaned_response,
                "confidence": self._estimate_response_confidence(cleaned_response),
                "parsed_successfully": True,
                "raw_response": raw_response
            }

        except Exception as e:
            self.logger.error(f"Error parsing {reasoner_name} response: {e}")
            return {
                "reasoner_name": reasoner_name,
                "reasoning": f"Error parsing response: {str(e)}",
                "confidence": 0.0,
                "parsed_successfully": False,
                "error": str(e),
                "raw_response": raw_response
            }

    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from a response that may contain additional text.

        Args:
            response: Raw response text

        Returns:
            Extracted JSON data or None if not found
        """
        try:
            # Method 1: Look for JSON code blocks
            json_block_pattern = r'```json\s*(.*?)\s*```'
            json_match = re.search(json_block_pattern, response, re.DOTALL | re.IGNORECASE)

            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

            # Method 2: Find JSON objects by braces
            brace_pattern = r'\{.*\}'
            brace_match = re.search(brace_pattern, response, re.DOTALL)

            if brace_match:
                json_str = brace_match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    fixed_json = self._fix_common_json_issues(json_str)
                    try:
                        return json.loads(fixed_json)
                    except json.JSONDecodeError:
                        pass

            # Method 3: Try parsing the entire response as JSON
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                pass

            return None

        except Exception as e:
            self.logger.warning(f"Error extracting JSON from response: {e}")
            return None

    def _fix_common_json_issues(self, json_str: str) -> str:
        """
        Fix common JSON formatting issues.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Fixed JSON string
        """
        try:
            # Remove trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)

            # Fix unquoted keys
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)

            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')

            # Remove comments
            json_str = re.sub(r'//.*', '', json_str)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

            return json_str

        except Exception:
            return json_str

    def _parse_json_structure(self, json_data: Dict[str, Any], raw_response: str) -> CouncilDecision:
        """
        Parse and validate JSON structure into CouncilDecision.

        Args:
            json_data: Extracted JSON data
            raw_response: Original raw response for fallback

        Returns:
            Validated CouncilDecision
        """
        try:
            # Extract required fields with defaults
            response_text = json_data.get("response", "")
            if not response_text:
                response_text = self._extract_response_from_raw(raw_response)

            actions = json_data.get("actions", [])
            if not isinstance(actions, list):
                actions = []

            mood = json_data.get("mood", "neutral")
            reasoning = json_data.get("reasoning", "")

            # Extract council reasoning
            council_reasoning = json_data.get("council_reasoning", {})
            if not isinstance(council_reasoning, dict):
                council_reasoning = {}

            # Validate and clean actions
            validated_actions = self._validate_actions(actions)

            # Calculate confidence based on response completeness
            confidence = self._calculate_response_confidence(json_data, raw_response)

            return CouncilDecision(
                response=response_text,
                actions=validated_actions,
                mood=mood,
                reasoning=reasoning,
                council_reasoning=council_reasoning,
                confidence=confidence,
                metadata={
                    "parsed_from_json": True,
                    "original_actions_count": len(actions),
                    "validated_actions_count": len(validated_actions),
                    "has_council_reasoning": bool(council_reasoning)
                }
            )

        except Exception as e:
            self.logger.error(f"Error parsing JSON structure: {e}")
            return self._create_fallback_decision(raw_response)

    def _validate_actions(self, actions: List[Any]) -> List[Dict[str, Any]]:
        """
        Validate and clean action objects.

        Args:
            actions: List of action objects to validate

        Returns:
            List of validated action dictionaries
        """
        validated_actions = []

        for action in actions:
            try:
                if not isinstance(action, dict):
                    continue

                # Required fields
                action_type = action.get("type", "")
                if not action_type:
                    continue

                # Valid action types
                valid_types = [
                    "move", "interact", "state_change", "pick_up", "put_down", "expression"
                ]

                if action_type not in valid_types:
                    # Try to map similar action types
                    type_mappings = {
                        "movement": "move",
                        "interaction": "interact",
                        "manipulation": "pick_up",
                        "emotion": "expression",
                        "mood": "expression"
                    }
                    action_type = type_mappings.get(action_type, "expression")

                validated_action = {
                    "type": action_type,
                    "target": action.get("target"),
                    "parameters": action.get("parameters", {})
                }

                # Ensure parameters is a dictionary
                if not isinstance(validated_action["parameters"], dict):
                    validated_action["parameters"] = {}

                validated_actions.append(validated_action)

            except Exception as e:
                self.logger.warning(f"Error validating action: {e}")
                continue

        return validated_actions[:5]  # Limit to 5 actions maximum

    def _calculate_response_confidence(self, json_data: Dict[str, Any], raw_response: str) -> float:
        """
        Calculate confidence score based on response completeness and quality.

        Args:
            json_data: Parsed JSON data
            raw_response: Original raw response

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            confidence = 0.5  # Base confidence

            # Check for required fields
            if json_data.get("response"):
                confidence += 0.2

            if json_data.get("council_reasoning"):
                council_reasoning = json_data["council_reasoning"]
                if isinstance(council_reasoning, dict) and len(council_reasoning) >= 3:
                    confidence += 0.2

            if json_data.get("actions") and isinstance(json_data["actions"], list):
                confidence += 0.1

            # Check response quality
            response_text = json_data.get("response", "")
            if len(response_text) > 20 and not any(word in response_text.lower()
                                                  for word in ["error", "failed", "unable"]):
                confidence += 0.1

            # Check for proper JSON formatting
            if "```json" in raw_response or raw_response.strip().startswith("{"):
                confidence += 0.1

            return min(1.0, confidence)

        except Exception:
            return 0.3

    def _extract_response_from_raw(self, raw_response: str) -> str:
        """
        Extract a reasonable response from raw text when JSON parsing fails.

        Args:
            raw_response: Raw response text

        Returns:
            Extracted response text
        """
        try:
            # Remove JSON markers and common prefixes
            cleaned = raw_response.strip()
            cleaned = re.sub(r'```json.*?```', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'\{.*?\}', '', cleaned, flags=re.DOTALL)
            cleaned = cleaned.strip()

            # Look for sentences that could be responses
            sentences = re.split(r'[.!?]+', cleaned)
            meaningful_sentences = [
                s.strip() for s in sentences
                if len(s.strip()) > 10 and not s.strip().lower().startswith(('json', 'response:', 'answer:'))
            ]

            if meaningful_sentences:
                return meaningful_sentences[0] + "."

            # Fallback
            return "I understand your request and will help you with that."

        except Exception:
            return "I understand your request and will help you with that."

    def _clean_response_text(self, response: str) -> str:
        """
        Clean response text for individual reasoner responses.

        Args:
            response: Raw response text

        Returns:
            Cleaned response text
        """
        try:
            # Remove common formatting artifacts
            cleaned = response.strip()
            cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # Remove bold markdown
            cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)      # Remove italic markdown
            cleaned = re.sub(r'#+\s*', '', cleaned)             # Remove headers

            # Remove excessive whitespace
            cleaned = re.sub(r'\n+', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)

            return cleaned.strip()

        except Exception:
            return response.strip()

    def _estimate_response_confidence(self, response: str) -> float:
        """
        Estimate confidence for individual reasoner responses.

        Args:
            response: Response text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            if not response or len(response) < 10:
                return 0.2

            confidence = 0.6  # Base confidence

            # Length-based scoring
            if len(response) > 50:
                confidence += 0.1
            if len(response) > 150:
                confidence += 0.1

            # Content quality indicators
            if any(word in response.lower() for word in ["analyze", "consider", "suggest", "recommend"]):
                confidence += 0.1

            # Negative indicators
            if any(word in response.lower() for word in ["error", "unable", "cannot", "failed"]):
                confidence -= 0.2

            return max(0.1, min(1.0, confidence))

        except Exception:
            return 0.5

    def _create_fallback_decision(self, raw_response: str) -> CouncilDecision:
        """
        Create a fallback decision when parsing fails.

        Args:
            raw_response: Original raw response

        Returns:
            Fallback CouncilDecision
        """
        try:
            # Extract any meaningful text from the response
            response_text = self._extract_response_from_raw(raw_response)

            return CouncilDecision(
                response=response_text,
                actions=[{
                    "type": "expression",
                    "target": "thoughtful",
                    "parameters": {}
                }],
                mood="thoughtful",
                reasoning="Response parsed using fallback method due to formatting issues",
                council_reasoning={
                    "fallback": "Could not parse structured reasoning from response"
                },
                confidence=0.4,
                metadata={
                    "parsed_from_json": False,
                    "fallback_used": True,
                    "raw_response_length": len(raw_response)
                }
            )

        except Exception as e:
            self.logger.error(f"Error creating fallback decision: {e}")
            return self._create_error_decision(raw_response, str(e))

    def _create_error_decision(self, raw_response: str, error_msg: str) -> CouncilDecision:
        """
        Create an error decision when all parsing fails.

        Args:
            raw_response: Original raw response
            error_msg: Error message

        Returns:
            Error CouncilDecision
        """
        return CouncilDecision(
            response="I understand what you're asking, but I'm having trouble processing my thoughts right now. Let me try a different approach.",
            actions=[],
            mood="confused",
            reasoning=f"Response parsing failed: {error_msg}",
            council_reasoning={
                "error": f"Parsing error: {error_msg}",
                "raw_response_length": len(raw_response)
            },
            confidence=0.1,
            metadata={
                "parsed_from_json": False,
                "error_occurred": True,
                "error_message": error_msg
            }
        )


# Global instance for easy access
response_parser = ResponseParser()