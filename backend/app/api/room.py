"""
API endpoints for room object management.

Provides endpoints for:
- Managing room objects (create, move, delete)
- Storage closet operations
- Object state management
- Collision detection
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
import logging

from ..services.room_service import room_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/room", tags=["room"])


@router.get("/objects", response_model=List[Dict[str, Any]])
async def get_room_objects():
    """Get all objects currently in the room."""
    try:
        objects = await room_service.get_all_objects()
        return objects
    except Exception as e:
        logger.error(f"Error getting room objects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve room objects")


@router.get("/objects/{object_id}", response_model=Dict[str, Any])
async def get_object(object_id: str):
    """Get a specific object by ID."""
    try:
        obj = await room_service.get_object_by_id(object_id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
        return obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve object")


@router.post("/objects", response_model=Dict[str, Any])
async def create_object(object_data: Dict[str, Any] = Body(...)):
    """Create a new object in the room."""
    try:
        obj = await room_service.create_object(object_data)
        return obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating object: {e}")
        raise HTTPException(status_code=500, detail="Failed to create object")


@router.put("/objects/{object_id}/move")
async def move_object(object_id: str, position: Dict[str, int] = Body(...)):
    """Move an object to a new position."""
    try:
        if "x" not in position or "y" not in position:
            raise ValueError("Position must include x and y coordinates")

        obj = await room_service.move_object(object_id, position["x"], position["y"])
        return obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error moving object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to move object")


@router.delete("/objects/{object_id}")
async def delete_object(object_id: str):
    """Remove an object from the room."""
    try:
        deleted = await room_service.delete_object(object_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Object {object_id} not found")
        return {"message": f"Object {object_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete object")


@router.put("/objects/{object_id}/state")
async def set_object_state(
    object_id: str,
    state_data: Dict[str, str] = Body(...)
):
    """Set or update an object's state."""
    try:
        if "key" not in state_data or "value" not in state_data:
            raise ValueError("State data must include key and value")

        updated_by = state_data.get("updated_by", "user")
        success = await room_service.set_object_state(
            object_id,
            state_data["key"],
            state_data["value"],
            updated_by
        )

        if success:
            return {"message": f"State {state_data['key']} updated for {object_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update state")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting state for object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update object state")


@router.get("/objects/{object_id}/states", response_model=Dict[str, str])
async def get_object_states(object_id: str):
    """Get all states for an object."""
    try:
        states = await room_service.get_object_states(object_id)
        return states
    except Exception as e:
        logger.error(f"Error getting states for object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve object states")


# Storage Closet Endpoints
@router.get("/storage", response_model=List[Dict[str, Any]])
async def get_storage_items():
    """Get all items in the storage closet."""
    try:
        items = await room_service.get_storage_items()
        return items
    except Exception as e:
        logger.error(f"Error getting storage items: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve storage items")


@router.post("/storage", response_model=Dict[str, Any])
async def add_to_storage(item_data: Dict[str, Any] = Body(...)):
    """Add an item to the storage closet."""
    try:
        item = await room_service.add_to_storage(item_data)
        return item
    except Exception as e:
        logger.error(f"Error adding item to storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to add item to storage")


@router.post("/storage/{item_id}/place")
async def place_from_storage(item_id: str, position: Dict[str, int] = Body(...)):
    """Place an item from storage into the room."""
    try:
        if "x" not in position or "y" not in position:
            raise ValueError("Position must include x and y coordinates")

        obj = await room_service.place_from_storage(item_id, position["x"], position["y"])
        return obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error placing item {item_id} from storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to place item from storage")


@router.post("/objects/{object_id}/store")
async def store_object(object_id: str):
    """Move an object from the room to storage."""
    try:
        item = await room_service.store_object(object_id)
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error storing object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store object")


# Utility Endpoints
@router.post("/initialize")
async def initialize_room():
    """Initialize the room with default objects."""
    try:
        await room_service.initialize_default_objects()
        return {"message": "Room initialized with default objects"}
    except Exception as e:
        logger.error(f"Error initializing room: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize room")


@router.get("/layout", response_model=Dict[str, Any])
async def get_room_layout():
    """Get the current room layout information."""
    try:
        # For now, return hardcoded layout info
        # This can be expanded to use the RoomLayout model later
        return {
            "id": "default",
            "name": "Default Room",
            "grid_size": {"width": 64, "height": 16},
            "cell_size": {"width": 20, "height": 30},
            "theme": {
                "background": "#1a1a1a",
                "grid": "#374151"
            }
        }
    except Exception as e:
        logger.error(f"Error getting room layout: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room layout")