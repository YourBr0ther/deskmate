"""
Conversation Memory API endpoints.

Provides endpoints for managing and inspecting conversation memory.
"""

from fastapi import APIRouter, Body
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

from app.services.conversation_memory import conversation_memory
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/memory/stats")
async def get_memory_stats() -> Dict[str, Any]:
    """Get conversation memory statistics."""
    try:
        memory_stats = conversation_memory.get_stats()
        embedding_stats = embedding_service.get_cache_stats()

        return {
            "status": "success",
            "memory": memory_stats,
            "embeddings": embedding_stats
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/memory/summary")
async def get_conversation_summary() -> Dict[str, Any]:
    """Get a summary of the current conversation."""
    try:
        summary = await conversation_memory.get_conversation_summary()

        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        return {
            "status": "error",
            "error": str(e),
            "summary": "Unable to generate summary."
        }


@router.post("/memory/clear")
async def clear_conversation_memory() -> Dict[str, Any]:
    """Clear current conversation memory (start fresh)."""
    try:
        conversation_id = await conversation_memory.initialize_conversation()

        return {
            "status": "success",
            "message": "Conversation memory cleared",
            "conversation_id": conversation_id
        }
    except Exception as e:
        logger.error(f"Error clearing conversation memory: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/memory/clear-all")
async def clear_all_conversation_memory() -> Dict[str, Any]:
    """Clear ALL conversation memory including vector database (DESTRUCTIVE)."""
    try:
        success = await conversation_memory.clear_all_memory()

        if success:
            # Start fresh conversation
            conversation_id = await conversation_memory.initialize_conversation()
            return {
                "status": "success",
                "message": "All conversation memory cleared (including vector database)",
                "conversation_id": conversation_id
            }
        else:
            return {
                "status": "error",
                "error": "Failed to clear all memory"
            }
    except Exception as e:
        logger.error(f"Error clearing all conversation memory: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/memory/clear-persona")
async def clear_persona_memory(persona_name: str) -> Dict[str, Any]:
    """Clear conversation memory for a specific persona."""
    try:
        if not persona_name:
            return {
                "status": "error",
                "error": "Persona name required"
            }

        success = await conversation_memory.clear_persona_memory(persona_name)

        if success:
            return {
                "status": "success",
                "message": f"Cleared memory for persona: {persona_name}"
            }
        else:
            return {
                "status": "error",
                "error": f"Failed to clear memory for persona: {persona_name}"
            }
    except Exception as e:
        logger.error(f"Error clearing persona memory: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/history")
async def get_chat_history(limit: int = 50) -> Dict[str, Any]:
    """Get chat history for frontend display."""
    try:
        history = await conversation_memory.get_chat_history_for_frontend(limit)

        return {
            "status": "success",
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return {
            "status": "error",
            "error": str(e),
            "messages": [],
            "count": 0
        }


@router.post("/initialize")
async def initialize_conversation_with_persona(
    request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Initialize conversation for a specific persona."""
    # Input validation
    if not isinstance(request, dict):
        return {
            "status": "error",
            "error": "Request body must be a JSON object",
            "conversation_id": None,
            "messages": [],
            "count": 0
        }

    persona_name = request.get("persona_name")
    load_history = request.get("load_history", True)

    # Validate persona_name if provided
    if persona_name is not None and (not isinstance(persona_name, str) or not persona_name.strip()):
        return {
            "status": "error",
            "error": "persona_name must be a non-empty string",
            "conversation_id": None,
            "messages": [],
            "count": 0
        }

    try:
        conversation_id = await conversation_memory.initialize_conversation(
            persona_name=persona_name,
            load_history=load_history
        )

        # Get the loaded history for frontend
        history = await conversation_memory.get_chat_history_for_frontend(persona_name=persona_name)

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "persona_name": persona_name,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error initializing conversation with persona: {e}")
        return {
            "status": "error",
            "error": str(e),
            "conversation_id": None,
            "messages": [],
            "count": 0
        }


# Pydantic models for embedding endpoints
class EmbeddingRequest(BaseModel):
    text: str

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]

class SimilarityRequest(BaseModel):
    text1: str
    text2: str


@router.post("/embeddings/generate")
async def generate_embedding(request: EmbeddingRequest) -> Dict[str, Any]:
    """Generate embedding for text using the new embedding service."""
    try:
        result = await embedding_service.generate_embedding_detailed(request.text)

        return {
            "status": "success",
            "embedding": result.embedding,
            "metadata": {
                "provider": result.provider.value,
                "model_name": result.model_name,
                "tokens_used": result.tokens_used,
                "cache_hit": result.cache_hit,
                "embedding_dimension": len(result.embedding)
            }
        }
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/embeddings/batch")
async def generate_batch_embeddings(request: BatchEmbeddingRequest) -> Dict[str, Any]:
    """Generate embeddings for multiple texts."""
    try:
        embeddings = await embedding_service.batch_generate_embeddings(request.texts)

        return {
            "status": "success",
            "embeddings": embeddings,
            "count": len(embeddings),
            "metadata": {
                "embedding_dimension": len(embeddings[0]) if embeddings else 0
            }
        }
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/embeddings/similarity")
async def calculate_similarity(request: SimilarityRequest) -> Dict[str, Any]:
    """Calculate semantic similarity between two texts."""
    try:
        # Generate embeddings for both texts
        embedding1 = await embedding_service.generate_embedding(request.text1)
        embedding2 = await embedding_service.generate_embedding(request.text2)

        # Calculate similarity
        similarity = embedding_service.calculate_similarity(embedding1, embedding2)

        return {
            "status": "success",
            "similarity": similarity,
            "texts": {
                "text1": request.text1,
                "text2": request.text2
            }
        }
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/embeddings/stats")
async def get_embedding_stats() -> Dict[str, Any]:
    """Get comprehensive embedding service statistics."""
    try:
        stats = embedding_service.get_stats()
        health = embedding_service.get_health_status()

        return {
            "status": "success",
            "stats": stats,
            "health": health
        }
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/embeddings/clear-cache")
async def clear_embedding_cache() -> Dict[str, Any]:
    """Clear the embedding cache."""
    try:
        embedding_service.clear_cache()

        return {
            "status": "success",
            "message": "Embedding cache cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing embedding cache: {e}")
        return {
            "status": "error",
            "error": str(e)
        }