"""
API endpoints for assistant management and movement.

Provides endpoints for:
- Getting assistant current state
- Moving assistant to positions
- Furniture interactions (sitting)
- Pathfinding and reachability queries
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Body
import logging

from app.services.assistant_service import assistant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/state")
async def get_assistant_state():
    """Get current assistant state including position, mood, and activity."""
    try:
        assistant = await assistant_service.get_assistant_state()
        return assistant.to_dict()
    except Exception as e:
        logger.error(f"Error getting assistant state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get assistant state")


@router.put("/position")
async def update_assistant_position(position_data: Dict[str, Any] = Body(...)):
    """
    Update assistant position directly.

    Body:
        {
            "x": int,
            "y": int,
            "facing": "up|down|left|right" (optional),
            "action": "idle|walking|sitting" (optional)
        }
    """
    try:
        x = position_data.get("x")
        y = position_data.get("y")
        facing = position_data.get("facing")
        action = position_data.get("action", "idle")

        if x is None or y is None:
            raise HTTPException(status_code=400, detail="Position x and y are required")

        if not (0 <= x < 64 and 0 <= y < 16):
            raise HTTPException(status_code=400, detail="Position must be within grid bounds (0-63, 0-15)")

        result = await assistant_service.update_assistant_position(x, y, facing, action)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assistant position: {e}")
        raise HTTPException(status_code=500, detail="Failed to update position")


@router.post("/move")
async def move_assistant(move_data: Dict[str, Any] = Body(...)):
    """
    Move assistant to target position using pathfinding.

    Body:
        {
            "target": {"x": int, "y": int},
            "validate_path": bool (optional, default true)
        }
    """
    try:
        target = move_data.get("target")
        validate_path = move_data.get("validate_path", True)

        if not target or "x" not in target or "y" not in target:
            raise HTTPException(status_code=400, detail="Target position with x and y coordinates required")

        target_x = target["x"]
        target_y = target["y"]

        if not (0 <= target_x < 64 and 0 <= target_y < 16):
            raise HTTPException(status_code=400, detail="Target position must be within grid bounds")

        result = await assistant_service.move_assistant_to(target_x, target_y, validate_path)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving assistant: {e}")
        raise HTTPException(status_code=500, detail="Failed to move assistant")


@router.post("/sit")
async def sit_on_furniture(sit_data: Dict[str, str] = Body(...)):
    """
    Make assistant sit on specified furniture.

    Body:
        {
            "furniture_id": "bed|desk|chair"
        }
    """
    try:
        furniture_id = sit_data.get("furniture_id")

        if not furniture_id:
            raise HTTPException(status_code=400, detail="Furniture ID is required")

        result = await assistant_service.sit_on_furniture(furniture_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sitting on furniture: {e}")
        raise HTTPException(status_code=500, detail="Failed to sit on furniture")


@router.get("/reachable")
async def get_reachable_positions():
    """Get all positions reachable by the assistant from current location."""
    try:
        reachable = await assistant_service.get_reachable_positions()

        # Convert set of tuples to list of dictionaries
        reachable_list = [{"x": x, "y": y} for x, y in reachable]

        return {
            "current_position": (await assistant_service.get_assistant_state()).to_dict()["position"],
            "reachable_positions": reachable_list,
            "count": len(reachable_list)
        }

    except Exception as e:
        logger.error(f"Error getting reachable positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reachable positions")


@router.post("/pathfind")
async def find_path_to_position(path_data: Dict[str, Any] = Body(...)):
    """
    Find path from current position to target without moving.

    Body:
        {
            "target": {"x": int, "y": int}
        }
    """
    try:
        from app.services.pathfinding import pathfinding_service

        target = path_data.get("target")
        if not target or "x" not in target or "y" not in target:
            raise HTTPException(status_code=400, detail="Target position required")

        target_x, target_y = target["x"], target["y"]
        if not (0 <= target_x < 64 and 0 <= target_y < 16):
            raise HTTPException(status_code=400, detail="Target position must be within grid bounds")

        # Get current assistant position
        assistant = await assistant_service.get_assistant_state()
        start_pos = (assistant.position_x, assistant.position_y)
        target_pos = (target_x, target_y)

        # Get obstacles
        obstacles = await assistant_service._get_room_obstacles()

        # Find path
        path = pathfinding_service.find_path(start_pos, target_pos, obstacles)

        return {
            "start": {"x": start_pos[0], "y": start_pos[1]},
            "target": {"x": target_pos[0], "y": target_pos[1]},
            "path": [{"x": x, "y": y} for x, y in path],
            "path_found": len(path) > 0,
            "path_length": len(path)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding path: {e}")
        raise HTTPException(status_code=500, detail="Failed to find path")


@router.get("/actions/log")
async def get_action_log(limit: int = 50):
    """Get recent assistant action log for debugging."""
    try:
        from sqlalchemy import select
        from app.models.assistant import AssistantActionLog
        from app.db.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            stmt = select(AssistantActionLog).order_by(
                AssistantActionLog.created_at.desc()
            ).limit(limit)
            result = await session.execute(stmt)
            actions = result.scalars().all()

            return {
                "actions": [action.to_dict() for action in actions],
                "count": len(actions)
            }

    except Exception as e:
        logger.error(f"Error getting action log: {e}")
        raise HTTPException(status_code=500, detail="Failed to get action log")


@router.post("/pick-up/{object_id}")
async def pick_up_object(object_id: str):
    """
    Pick up a movable object by ID.

    Args:
        object_id: ID of the object to pick up

    Returns:
        Action execution result with success status
    """
    try:
        from app.services.action_executor import action_executor

        if not object_id:
            raise HTTPException(status_code=400, detail="Object ID is required")

        # Create pick up action
        action = {
            "type": "pick_up",
            "target": object_id,
            "parameters": {}
        }

        # Execute the action
        result = await action_executor.execute_single_action(action)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error picking up object {object_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pick up object")


@router.post("/put-down")
async def put_down_object(put_down_data: Dict[str, Any] = Body(None)):
    """
    Put down the currently held object.

    Body (optional):
        {
            "position": {"x": int, "y": int}  // Target position, defaults to assistant location
        }

    Returns:
        Action execution result with success status
    """
    try:
        from app.services.action_executor import action_executor

        # Get assistant state to check if holding something
        assistant = await assistant_service.get_assistant_state()
        if not assistant.holding_object_id:
            raise HTTPException(status_code=400, detail="Not holding any object")

        # Parse target position if provided
        target = None
        if put_down_data and "position" in put_down_data:
            position = put_down_data["position"]
            if "x" in position and "y" in position:
                target = {"x": position["x"], "y": position["y"]}
                # Validate position bounds
                if not (0 <= target["x"] < 64 and 0 <= target["y"] < 16):
                    raise HTTPException(status_code=400, detail="Position must be within grid bounds (0-63, 0-15)")

        # Create put down action
        action = {
            "type": "put_down",
            "target": target,
            "parameters": {}
        }

        # Execute the action
        result = await action_executor.execute_single_action(action)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error putting down object: {e}")
        raise HTTPException(status_code=500, detail="Failed to put down object")


@router.get("/holding")
async def get_holding_status():
    """
    Get information about what object the assistant is currently holding.

    Returns:
        {
            "holding_object_id": str | null,
            "holding_object_name": str | null,
            "holding_object": dict | null  // Full object details if holding something
        }
    """
    try:
        from app.services.room_service import room_service

        assistant = await assistant_service.get_assistant_state()
        holding_object_id = assistant.holding_object_id

        if not holding_object_id:
            return {
                "holding_object_id": None,
                "holding_object_name": None,
                "holding_object": None
            }

        # Get object details
        objects = await room_service.get_all_objects()
        held_object = next((obj for obj in objects if obj["id"] == holding_object_id), None)

        return {
            "holding_object_id": holding_object_id,
            "holding_object_name": held_object["name"] if held_object else "Unknown",
            "holding_object": held_object
        }

    except Exception as e:
        logger.error(f"Error getting holding status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get holding status")