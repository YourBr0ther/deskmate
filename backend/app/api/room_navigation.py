"""
API endpoints for multi-room navigation and floor plan management.

This module provides REST endpoints for:
- Room navigation and movement
- Floor plan template management
- Room and doorway information
- Navigation status and control
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import logging

from app.db.database import get_db
from app.models.assistant import AssistantState
from app.models.rooms import FloorPlan, Room, Doorway, FurnitureItem
from app.services.room_navigation import room_navigation_service
from app.services.multi_room_pathfinding import multi_room_pathfinding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooms", tags=["room-navigation"])


# Request/Response Models
class NavigateRequest(BaseModel):
    target_x: float = Field(..., description="Target X coordinate in pixels")
    target_y: float = Field(..., description="Target Y coordinate in pixels")
    target_room_id: Optional[str] = Field(None, description="Target room ID (optional)")
    assistant_id: str = Field(default="default", description="Assistant identifier")


class NavigationResponse(BaseModel):
    success: bool
    navigation_id: Optional[str] = None
    path: List[Dict[str, Any]] = []
    room_transitions: List[Dict[str, Any]] = []
    doors_opened: List[Dict[str, Any]] = []
    estimated_duration: float = 0.0
    total_distance: float = 0.0
    error: Optional[str] = None


class FloorPlanResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    dimensions: Dict[str, Any]
    rooms: List[Dict[str, Any]]
    walls: List[Dict[str, Any]]
    doorways: List[Dict[str, Any]]
    furniture: List[Dict[str, Any]]


class RoomListResponse(BaseModel):
    rooms: List[Dict[str, Any]]
    current_room_id: Optional[str]
    current_floor_plan_id: Optional[str]


# Navigation Endpoints
@router.post("/navigate", response_model=NavigationResponse)
async def navigate_to_position(
    request: NavigateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Navigate assistant to specified position with automatic room transitions."""
    try:
        result = await room_navigation_service.navigate_to_position(
            db=db,
            assistant_id=request.assistant_id,
            target_x=request.target_x,
            target_y=request.target_y,
            target_room_id=request.target_room_id,
            user_initiated=True
        )

        return NavigationResponse(**result)

    except Exception as e:
        logger.error(f"Error navigating assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Navigation failed: {str(e)}")


@router.get("/navigation/status/{assistant_id}")
async def get_navigation_status(assistant_id: str = "default"):
    """Get current navigation status for assistant."""
    try:
        navigation = room_navigation_service.get_active_navigation(assistant_id)

        if not navigation:
            return {"active": False, "message": "No active navigation"}

        return {
            "active": True,
            "navigation_id": navigation["id"],
            "current_step": navigation["current_step"],
            "total_steps": len(navigation["path"]),
            "target_position": navigation["target_position"],
            "target_room_id": navigation["target_room_id"],
            "estimated_remaining": navigation["estimated_duration"] * (
                1 - navigation["current_step"] / len(navigation["path"])
            ),
            "user_initiated": navigation["user_initiated"]
        }

    except Exception as e:
        logger.error(f"Error getting navigation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/navigation/cancel/{navigation_id}")
async def cancel_navigation(navigation_id: str):
    """Cancel active navigation."""
    try:
        success = room_navigation_service.cancel_navigation(navigation_id)

        if success:
            return {"success": True, "message": "Navigation cancelled"}
        else:
            return {"success": False, "message": "Navigation not found or already completed"}

    except Exception as e:
        logger.error(f"Error cancelling navigation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")


# Template Discovery and Loading
@router.get("/templates/discover")
async def discover_templates():
    """Discover available template files in the templates directory."""
    try:
        from app.services.template_loader import template_loader_service
        templates = template_loader_service.discover_templates()

        return {
            "templates": templates,
            "count": len(templates),
            "templates_directory": str(template_loader_service.templates_directory)
        }

    except Exception as e:
        logger.error(f"Error discovering templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to discover templates: {str(e)}")


@router.post("/templates/load-all")
async def load_all_templates(db: Session = Depends(get_db)):
    """Load all discovered templates into the database."""
    try:
        from app.services.template_loader import template_loader_service
        results = template_loader_service.load_all_templates(db)

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        return {
            "success": True,
            "message": f"Loaded {success_count}/{total_count} templates",
            "results": results,
            "summary": {
                "total": total_count,
                "loaded": success_count,
                "failed": total_count - success_count
            }
        }

    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load templates: {str(e)}")


@router.post("/templates/load/{template_file}")
async def load_single_template(template_file: str, db: Session = Depends(get_db)):
    """Load a single template file into the database."""
    try:
        from app.services.template_loader import template_loader_service

        # Load template data from file
        template_data = template_loader_service.load_template_from_file(template_file)
        if not template_data:
            raise HTTPException(status_code=404, detail=f"Template file {template_file} not found or invalid")

        # Validate template data
        errors = template_loader_service.validate_template_data(template_data)
        if errors:
            return {
                "success": False,
                "errors": errors,
                "template_id": template_data.get("id", "unknown")
            }

        # Load to database
        success = template_loader_service.load_template_to_database(db, template_data)

        return {
            "success": success,
            "template_id": template_data["id"],
            "template_name": template_data["name"],
            "message": f"Template {template_data['id']} loaded successfully" if success else "Failed to load template"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading template {template_file}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load template: {str(e)}")


# Floor Plan Management
@router.get("/floor-plans", response_model=List[Dict[str, Any]])
async def get_floor_plans(db: Session = Depends(get_db)):
    """Get all available floor plan templates."""
    try:
        floor_plans = db.query(FloorPlan).filter(FloorPlan.is_template == True).all()

        return [
            {
                "id": fp.id,
                "name": fp.name,
                "description": fp.description,
                "category": fp.category,
                "dimensions": {
                    "width": fp.width,
                    "height": fp.height,
                    "scale": fp.scale,
                    "units": fp.units
                },
                "is_active": fp.is_active,
                "room_count": len(fp.rooms),
                "created_by": fp.created_by,
                "version": fp.version
            }
            for fp in floor_plans
        ]

    except Exception as e:
        logger.error(f"Error getting floor plans: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get floor plans: {str(e)}")


@router.get("/floor-plans/{floor_plan_id}", response_model=FloorPlanResponse)
async def get_floor_plan(floor_plan_id: str, db: Session = Depends(get_db)):
    """Get detailed floor plan information."""
    try:
        floor_plan = db.query(FloorPlan).filter(FloorPlan.id == floor_plan_id).first()

        if not floor_plan:
            raise HTTPException(status_code=404, detail="Floor plan not found")

        return FloorPlanResponse(**floor_plan.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting floor plan {floor_plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get floor plan: {str(e)}")


@router.post("/floor-plans/{floor_plan_id}/activate")
async def activate_floor_plan(floor_plan_id: str, assistant_id: str = "default", db: Session = Depends(get_db)):
    """Activate a floor plan and move assistant to default position."""
    try:
        from app.services.template_loader import template_loader_service

        result = template_loader_service.activate_template(db, floor_plan_id, assistant_id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating floor plan {floor_plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate floor plan: {str(e)}")


@router.get("/floor-plans/active")
async def get_active_floor_plan(db: Session = Depends(get_db)):
    """Get the currently active floor plan."""
    try:
        active_floor_plan = db.query(FloorPlan).filter(FloorPlan.is_active == True).first()

        if not active_floor_plan:
            return {"active_floor_plan": None, "message": "No active floor plan"}

        return {
            "active_floor_plan": {
                "id": active_floor_plan.id,
                "name": active_floor_plan.name,
                "description": active_floor_plan.description,
                "category": active_floor_plan.category,
                "dimensions": {
                    "width": active_floor_plan.width,
                    "height": active_floor_plan.height,
                    "scale": active_floor_plan.scale,
                    "units": active_floor_plan.units
                },
                "room_count": len(active_floor_plan.rooms)
            }
        }

    except Exception as e:
        logger.error(f"Error getting active floor plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active floor plan: {str(e)}")


@router.post("/templates/validate")
async def validate_template(template_data: Dict[str, Any]):
    """Validate template data structure."""
    try:
        from app.services.template_loader import template_loader_service

        errors = template_loader_service.validate_template_data(template_data)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "template_id": template_data.get("id", "unknown"),
            "template_name": template_data.get("name", "unknown")
        }

    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate template: {str(e)}")


# Room Information
@router.get("/current", response_model=RoomListResponse)
async def get_current_rooms(assistant_id: str = "default", db: Session = Depends(get_db)):
    """Get current room information and available rooms."""
    try:
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()

        if not assistant or not assistant.current_floor_plan_id:
            return RoomListResponse(
                rooms=[],
                current_room_id=None,
                current_floor_plan_id=None
            )

        # Get all rooms in current floor plan
        rooms = db.query(Room).filter(Room.floor_plan_id == assistant.current_floor_plan_id).all()

        room_data = []
        for room in rooms:
            # Get furniture count
            furniture_count = db.query(FurnitureItem).filter(
                FurnitureItem.room_id == room.id
            ).count()

            # Get connected rooms via doorways
            connected_rooms = []
            doorways = db.query(Doorway).filter(
                (Doorway.room_a_id == room.id) | (Doorway.room_b_id == room.id),
                Doorway.is_accessible == True
            ).all()

            for doorway in doorways:
                connected_room_id = doorway.room_b_id if doorway.room_a_id == room.id else doorway.room_a_id
                connected_rooms.append({
                    "room_id": connected_room_id,
                    "doorway_id": doorway.id,
                    "doorway_name": doorway.name,
                    "requires_interaction": doorway.requires_interaction
                })

            room_info = room.to_dict()
            room_info.update({
                "furniture_count": furniture_count,
                "connected_rooms": connected_rooms,
                "is_current": room.id == assistant.current_room_id
            })
            room_data.append(room_info)

        return RoomListResponse(
            rooms=room_data,
            current_room_id=assistant.current_room_id,
            current_floor_plan_id=assistant.current_floor_plan_id
        )

    except Exception as e:
        logger.error(f"Error getting current rooms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rooms: {str(e)}")


@router.get("/doorways/{floor_plan_id}")
async def get_doorways(floor_plan_id: str, db: Session = Depends(get_db)):
    """Get all doorways in floor plan with position information."""
    try:
        doorways = db.query(Doorway).filter(Doorway.floor_plan_id == floor_plan_id).all()

        doorway_data = []
        for doorway in doorways:
            world_pos = doorway.get_world_position()
            doorway_info = doorway.to_dict()
            doorway_info["world_position"] = {"x": world_pos[0], "y": world_pos[1]}
            doorway_data.append(doorway_info)

        return {"doorways": doorway_data}

    except Exception as e:
        logger.error(f"Error getting doorways: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get doorways: {str(e)}")


# Pathfinding Utilities
@router.post("/pathfind/preview")
async def preview_path(
    request: NavigateRequest,
    db: Session = Depends(get_db)
):
    """Preview navigation path without executing movement."""
    try:
        assistant = db.query(AssistantState).filter(AssistantState.id == request.assistant_id).first()
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")

        if not assistant.current_floor_plan_id:
            raise HTTPException(status_code=400, detail="No active floor plan")

        target_room_id = request.target_room_id or assistant.current_room_id

        path_result = multi_room_pathfinding_service.find_multi_room_path(
            db=db,
            floor_plan_id=assistant.current_floor_plan_id,
            start_pos=(assistant.position_x, assistant.position_y),
            start_room_id=assistant.current_room_id,
            goal_pos=(request.target_x, request.target_y),
            goal_room_id=target_room_id
        )

        return {
            "success": bool(path_result["path"]),
            "path": path_result["path"],
            "room_transitions": path_result["room_transitions"],
            "doorways_to_open": path_result["doorways_to_open"],
            "estimated_duration": path_result["estimated_duration"],
            "total_distance": path_result["total_distance"],
            "waypoint_count": len(path_result["path"])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview path: {str(e)}")


# Assistant Position
@router.get("/assistant/position/{assistant_id}")
async def get_assistant_position(assistant_id: str = "default", db: Session = Depends(get_db)):
    """Get current assistant position and room information."""
    try:
        assistant = db.query(AssistantState).filter(AssistantState.id == assistant_id).first()

        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")

        return {
            "position": {"x": assistant.position_x, "y": assistant.position_y},
            "room_id": assistant.current_room_id,
            "floor_plan_id": assistant.current_floor_plan_id,
            "facing_direction": assistant.facing_direction,
            "facing_angle": assistant.facing_angle,
            "is_moving": assistant.is_moving,
            "current_action": assistant.current_action,
            "movement": {
                "target": {
                    "x": assistant.target_x,
                    "y": assistant.target_y,
                    "room_id": assistant.target_room_id
                } if assistant.target_x is not None else None,
                "speed": assistant.movement_speed
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assistant position: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")