"""
Brain Council API endpoints for AI reasoning system.

Provides endpoints for:
- Testing Brain Council reasoning
- Processing messages with contextual awareness
- Getting council analysis and decisions
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import logging

from app.services.brain_council import brain_council
from app.services.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brain", tags=["brain_council"])


@router.post("/process")
async def process_with_brain_council(request: Dict[str, Any] = Body(...)):
    """
    Process a message through the Brain Council reasoning system.

    Body:
        {
            "message": "user message",
            "persona_context": {
                "name": "persona name",
                "personality": "persona personality"
            }
        }

    Returns:
        {
            "response": "AI response text",
            "actions": [...list of actions...],
            "mood": "current mood",
            "reasoning": "explanation",
            "council_reasoning": {...detailed reasoning...}
        }
    """
    try:
        message = request.get("message", "").strip()
        persona_context = request.get("persona_context")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Add to conversation memory
        persona_name = persona_context.get("name") if persona_context else None
        await conversation_memory.add_user_message(message, persona_name)

        # Process through Brain Council
        logger.info(f"Processing message through Brain Council: {message[:50]}...")
        result = await brain_council.process_user_message(
            user_message=message,
            persona_context=persona_context
        )

        # Store assistant response in memory
        await conversation_memory.add_assistant_message(
            result.get("response", ""),
            persona_name,
            result.get("actions")
        )

        return {
            "success": True,
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Brain Council processing: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.get("/test")
async def test_brain_council():
    """
    Test Brain Council functionality with a simple message.

    Returns basic test results to verify the system is working.
    """
    try:
        test_message = "Hello, how are you today?"
        test_persona = {
            "name": "Test Assistant",
            "personality": "Friendly and helpful AI assistant"
        }

        result = await brain_council.process_user_message(
            user_message=test_message,
            persona_context=test_persona
        )

        return {
            "success": True,
            "test_message": test_message,
            "response": result.get("response"),
            "mood": result.get("mood"),
            "actions_count": len(result.get("actions", [])),
            "has_reasoning": bool(result.get("reasoning")),
            "has_council_reasoning": bool(result.get("council_reasoning"))
        }

    except Exception as e:
        logger.error(f"Brain Council test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "test_message": "Hello, how are you today?"
        }


@router.post("/analyze")
async def analyze_context(request: Dict[str, Any] = Body(...)):
    """
    Analyze the current context without generating a response.

    Useful for debugging and understanding what the Brain Council sees.

    Body:
        {
            "include_room_state": true,
            "include_memory": true,
            "persona_name": "optional persona name"
        }
    """
    try:
        include_room = request.get("include_room_state", True)
        include_memory = request.get("include_memory", True)
        persona_name = request.get("persona_name")

        analysis = {
            "success": True,
            "context": {}
        }

        # Get room context
        if include_room:
            try:
                context = await brain_council._gather_context()
                analysis["context"]["room"] = context
            except Exception as e:
                analysis["context"]["room_error"] = str(e)

        # Get memory context
        if include_memory:
            try:
                memory_context = await conversation_memory.get_conversation_context(
                    current_message="",
                    persona_name=persona_name
                )
                analysis["context"]["memory"] = {
                    "message_count": len(memory_context),
                    "recent_messages": [
                        {"role": msg.role, "content": msg.content[:100]}
                        for msg in memory_context[-5:]
                    ]
                }
            except Exception as e:
                analysis["context"]["memory_error"] = str(e)

        # Get stats
        analysis["stats"] = {
            "memory_stats": conversation_memory.get_stats(),
            "current_persona": persona_name
        }

        return analysis

    except Exception as e:
        logger.error(f"Context analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze context: {str(e)}")