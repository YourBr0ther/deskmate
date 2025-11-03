"""
Chat API endpoints for LLM integration.

Provides endpoints for:
- Chat completions with streaming support
- Model selection and management
- LLM provider testing
- Chat history and context management
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
import logging
import json
import uuid
from datetime import datetime

from app.services.llm_manager import llm_manager, ChatMessage, LLMProvider
from app.services.room_service import room_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/models")
async def get_available_models():
    """Get all available LLM models across providers."""
    try:
        models = await llm_manager.get_available_models()

        # Convert to API format
        model_list = []
        for model_id, model in models.items():
            model_list.append({
                "id": model.id,
                "name": model.name,
                "provider": model.provider.value,
                "description": model.description,
                "max_tokens": model.max_tokens,
                "context_window": model.context_window,
                "supports_streaming": model.supports_streaming,
                "cost_per_token": model.cost_per_token
            })

        return {
            "models": model_list,
            "current_model": llm_manager.current_model,
            "current_provider": llm_manager.current_provider.value
        }

    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")


@router.post("/model/select")
async def select_model(model_data: Dict[str, str] = Body(...)):
    """
    Select the current LLM model.

    Body:
        {
            "model_id": "model_identifier"
        }
    """
    try:
        model_id = model_data.get("model_id")
        if not model_id:
            raise HTTPException(status_code=400, detail="Model ID is required")

        success = await llm_manager.set_model(model_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Unknown model: {model_id}")

        return {
            "success": True,
            "current_model": llm_manager.current_model,
            "current_provider": llm_manager.current_provider.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting model: {e}")
        raise HTTPException(status_code=500, detail="Failed to select model")


@router.post("/completion")
async def chat_completion(chat_data: Dict[str, Any] = Body(...)):
    """
    Generate chat completion (non-streaming).

    Body:
        {
            "messages": [
                {"role": "user|assistant|system", "content": "message text"}
            ],
            "temperature": 0.7 (optional),
            "max_tokens": 1000 (optional)
        }
    """
    try:
        messages_data = chat_data.get("messages", [])
        temperature = chat_data.get("temperature", 0.7)
        max_tokens = chat_data.get("max_tokens")

        if not messages_data:
            raise HTTPException(status_code=400, detail="Messages are required")

        # Convert to ChatMessage objects
        messages = []
        for msg in messages_data:
            if "role" not in msg or "content" not in msg:
                raise HTTPException(status_code=400, detail="Each message must have 'role' and 'content'")

            messages.append(ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.now().isoformat()
            ))

        # Generate completion
        response = await llm_manager.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if response.error:
            raise HTTPException(status_code=500, detail=response.error)

        return {
            "content": response.content,
            "model": response.model,
            "provider": response.provider.value,
            "tokens_used": response.tokens_used,
            "finish_reason": response.finish_reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate completion")


@router.post("/completion/stream")
async def chat_completion_stream(chat_data: Dict[str, Any] = Body(...)):
    """
    Generate streaming chat completion.

    Body:
        {
            "messages": [
                {"role": "user|assistant|system", "content": "message text"}
            ],
            "temperature": 0.7 (optional),
            "max_tokens": 1000 (optional)
        }
    """
    try:
        messages_data = chat_data.get("messages", [])
        temperature = chat_data.get("temperature", 0.7)
        max_tokens = chat_data.get("max_tokens")

        if not messages_data:
            raise HTTPException(status_code=400, detail="Messages are required")

        # Convert to ChatMessage objects
        messages = []
        for msg in messages_data:
            if "role" not in msg or "content" not in msg:
                raise HTTPException(status_code=400, detail="Each message must have 'role' and 'content'")

            messages.append(ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.now().isoformat()
            ))

        # Create streaming generator
        async def generate_stream():
            try:
                async for chunk in llm_manager.chat_completion_stream(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    # Send chunk as Server-Sent Event
                    yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

                # Send completion signal
                yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/stream-event",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up streaming: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup streaming")


@router.get("/test/{provider}")
async def test_provider_connection(provider: str):
    """
    Test connection to LLM provider.

    Args:
        provider: 'nano_gpt' or 'ollama'
    """
    try:
        if provider not in ["nano_gpt", "ollama"]:
            raise HTTPException(status_code=400, detail="Invalid provider. Use 'nano_gpt' or 'ollama'")

        provider_enum = LLMProvider.NANO_GPT if provider == "nano_gpt" else LLMProvider.OLLAMA
        result = await llm_manager.test_connection(provider_enum)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to test provider connection")


@router.get("/status")
async def get_chat_status():
    """Get current chat system status."""
    try:
        # Test both providers
        nano_gpt_status = await llm_manager.test_connection(LLMProvider.NANO_GPT)
        ollama_status = await llm_manager.test_connection(LLMProvider.OLLAMA)

        return {
            "current_model": llm_manager.current_model,
            "current_provider": llm_manager.current_provider.value,
            "providers": {
                "nano_gpt": {
                    "available": nano_gpt_status["success"],
                    "error": nano_gpt_status.get("error"),
                    "models": nano_gpt_status.get("available_models", [])
                },
                "ollama": {
                    "available": ollama_status["success"],
                    "error": ollama_status.get("error"),
                    "models": ollama_status.get("available_models", [])
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat status")


@router.post("/simple")
async def simple_chat(chat_data: Dict[str, Any] = Body(...)):
    """
    Simple chat endpoint for quick testing.

    Body:
        {
            "message": "user message",
            "system_prompt": "optional system prompt",
            "temperature": 0.7 (optional)
        }
    """
    try:
        user_message = chat_data.get("message")
        system_prompt = chat_data.get("system_prompt", "You are a helpful AI assistant.")
        temperature = chat_data.get("temperature", 0.7)

        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Build messages
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_message)
        ]

        # Generate response
        response = await llm_manager.chat_completion(
            messages=messages,
            temperature=temperature
        )

        if response.error:
            return {
                "success": False,
                "error": response.error,
                "model": response.model,
                "provider": response.provider.value
            }

        return {
            "success": True,
            "response": response.content,
            "model": response.model,
            "provider": response.provider.value,
            "tokens_used": response.tokens_used
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.post("/command")
async def process_command(command_data: Dict[str, Any] = Body(...)):
    """
    Process chat commands like /create.

    Body:
        {
            "message": "/create a red coffee mug",
            "persona_name": "optional persona context"
        }
    """
    try:
        message = command_data.get("message", "").strip()
        persona_name = command_data.get("persona_name")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Check if it's a command
        if not message.startswith("/"):
            raise HTTPException(status_code=400, detail="Not a command - commands must start with /")

        # Parse command and arguments
        parts = message[1:].split(" ", 1)  # Remove / and split
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "create":
            return await _handle_create_command(args, persona_name)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: /{command}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        raise HTTPException(status_code=500, detail="Failed to process command")


async def _handle_create_command(description: str, persona_name: Optional[str] = None) -> Dict[str, Any]:
    """Handle the /create command to generate new objects."""
    if not description:
        raise HTTPException(status_code=400, detail="Description is required for /create command")

    try:
        # Create a system prompt for object generation
        system_prompt = """You are an object generator for a virtual room. Given a description, create a JSON object with the following properties:

{
  "name": "Short object name (2-4 words)",
  "description": "Detailed description of the object",
  "type": "decoration|item|tool",
  "default_size": {"width": 1-3, "height": 1-3},
  "color_scheme": "color name like 'red', 'blue', 'wood', 'metal'",
  "sprite_name": "suggested filename like 'coffee_mug.png'"
}

Make the object realistic and appropriate for a bedroom/living space. Keep sizes small (1-3 cells).
Respond ONLY with valid JSON."""

        # Generate object using LLM
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"Create an object: {description}")
        ]

        response = await llm_manager.chat_completion(
            messages=messages,
            temperature=0.3  # Lower temperature for more consistent results
        )

        if response.error:
            raise HTTPException(status_code=500, detail=f"LLM error: {response.error}")

        # Parse the JSON response
        try:
            # Clean up the response - remove markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            logger.info(f"LLM response for object creation: {content}")
            object_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {response.content}")
            # Create a fallback object if JSON parsing fails
            object_data = {
                "name": f"Generated Item",
                "description": f"A {description} created by the system",
                "type": "item",
                "default_size": {"width": 1, "height": 1},
                "color_scheme": "gray",
                "sprite_name": "generic_item.png"
            }

        # Validate required fields
        required_fields = ["name", "description", "type", "default_size", "color_scheme"]
        for field in required_fields:
            if field not in object_data:
                raise HTTPException(status_code=500, detail=f"Generated object missing field: {field}")

        # Generate unique ID and add metadata
        object_id = f"created_{uuid.uuid4().hex[:8]}"
        storage_data = {
            "id": object_id,
            "name": object_data["name"],
            "description": object_data["description"],
            "type": object_data["type"],
            "default_size": {
                "width": object_data["default_size"]["width"],
                "height": object_data["default_size"]["height"]
            },
            "color": object_data["color_scheme"],
            "sprite": object_data.get("sprite_name"),
            "created_by": "user"
        }

        if persona_name:
            storage_data["description"] += f" (Created by {persona_name})"

        # Add to storage using room service
        storage_item = await room_service.add_to_storage(storage_data)

        return {
            "success": True,
            "command": "create",
            "description": description,
            "created_object": storage_item,
            "message": f"Created '{storage_item['name']}' and added to storage closet!"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create command: {e}")
        raise HTTPException(status_code=500, detail="Failed to create object")