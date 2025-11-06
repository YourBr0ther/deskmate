"""
Frontend compatibility API endpoints.

Provides endpoints that match the frontend's expected API interface.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.rooms import FloorPlan, Room, Wall, FurnitureItem
from app.models.assistant import AssistantState
from app.services.template_loader import template_loader_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/floor-plans/current")
async def get_current_floor_plan(db: AsyncSession = Depends(get_db)):
    """Get the currently active floor plan for frontend compatibility."""
    try:
        # Get active floor plan
        stmt = select(FloorPlan).filter(FloorPlan.is_active == True)
        result = await db.execute(stmt)
        active_floor_plan = result.scalar_one_or_none()

        if not active_floor_plan:
            # Check if assistant is positioned in a "default" system
            stmt = select(AssistantState).filter(AssistantState.id == "default")
            result = await db.execute(stmt)
            assistant = result.scalar_one_or_none()

            if assistant and assistant.current_floor_plan_id == "default":
                # Return a minimal default floor plan for frontend compatibility
                return {
                    "id": "default",
                    "name": "Default Room",
                    "description": "Default room layout",
                    "dimensions": {
                        "width": 1920,
                        "height": 480,
                        "scale": 30,
                        "units": "pixels"
                    },
                    "rooms": [{
                        "id": "right",
                        "name": "Main Room",
                        "type": "living",
                        "bounds": {
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 480
                        },
                        "properties": {
                            "floor_color": "#f5f5f5",
                            "floor_material": "hardwood",
                            "lighting_level": 0.8,
                            "temperature": 72.0
                        },
                        "accessibility": {
                            "is_accessible": True
                        }
                    }],
                    "walls": [],
                    "furniture": [],
                    "styling": {
                        "background_color": "#f5f5f5",
                        "wall_color": "#333333",
                        "wall_thickness": 8
                    }
                }

            raise HTTPException(status_code=404, detail="No active floor plan")

        # Get rooms for this floor plan
        stmt = select(Room).filter(Room.floor_plan_id == active_floor_plan.id)
        result = await db.execute(stmt)
        rooms = result.scalars().all()

        # Get walls for this floor plan
        stmt = select(Wall).filter(Wall.floor_plan_id == active_floor_plan.id)
        result = await db.execute(stmt)
        walls = result.scalars().all()

        # Get furniture for this floor plan
        stmt = select(FurnitureItem).filter(FurnitureItem.floor_plan_id == active_floor_plan.id)
        result = await db.execute(stmt)
        furniture = result.scalars().all()

        # Build the response format expected by frontend
        floor_plan_data = {
            "id": active_floor_plan.id,
            "name": active_floor_plan.name,
            "description": active_floor_plan.description,
            "dimensions": {
                "width": active_floor_plan.width,
                "height": active_floor_plan.height,
                "scale": active_floor_plan.scale,
                "units": active_floor_plan.units
            },
            "rooms": [room.to_dict() for room in rooms],
            "walls": [wall.to_dict() for wall in walls],
            "furniture": [item.to_dict() for item in furniture],
            "styling": {
                "background_color": active_floor_plan.background_color,
                "wall_color": active_floor_plan.wall_color,
                "wall_thickness": active_floor_plan.wall_thickness
            }
        }

        return floor_plan_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current floor plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current floor plan: {str(e)}")


@router.post("/floor-plans/create-default")
async def create_default_floor_plan(db: AsyncSession = Depends(get_db)):
    """Create a default floor plan if none exists."""
    try:
        # Check if there are any floor plans
        stmt = select(FloorPlan)
        result = await db.execute(stmt)
        existing_floor_plans = result.scalars().all()

        if existing_floor_plans:
            # Activate the first available floor plan
            first_plan = existing_floor_plans[0]

            # Deactivate all floor plans first
            for fp in existing_floor_plans:
                fp.is_active = False

            # Activate the first one
            first_plan.is_active = True
            await db.commit()

            # Get the assistant and position them
            stmt = select(AssistantState).filter(AssistantState.id == "default")
            result = await db.execute(stmt)
            assistant = result.scalar_one_or_none()

            if assistant:
                # Get first room for positioning
                stmt = select(Room).filter(Room.floor_plan_id == first_plan.id)
                result = await db.execute(stmt)
                first_room = result.scalar_one_or_none()

                if first_room:
                    # Position assistant in center of first room
                    center_x = first_room.bounds_x + first_room.bounds_width / 2
                    center_y = first_room.bounds_y + first_room.bounds_height / 2

                    assistant.current_floor_plan_id = first_plan.id
                    assistant.current_room_id = first_room.id
                    assistant.position_x = center_x
                    assistant.position_y = center_y
                    assistant.is_moving = False

                    await db.commit()

            return {
                "id": first_plan.id,
                "name": first_plan.name,
                "message": "Activated existing floor plan"
            }
        else:
            # Try to load templates if no floor plans exist
            results = await template_loader_service.load_all_templates(db)
            success_count = sum(1 for success in results.values() if success)

            if success_count == 0:
                raise HTTPException(status_code=500, detail="No templates available and failed to create default floor plan")

            # Get the first successfully loaded floor plan and activate it
            stmt = select(FloorPlan)
            result = await db.execute(stmt)
            available_plans = result.scalars().all()

            if available_plans:
                # Use the template activation system
                first_plan = available_plans[0]
                activation_result = await template_loader_service.activate_template(db, first_plan.id, "default")

                if activation_result["success"]:
                    return {
                        "id": first_plan.id,
                        "name": first_plan.name,
                        "message": f"Created and activated template: {first_plan.name}"
                    }
                else:
                    raise HTTPException(status_code=500, detail=activation_result["error"])
            else:
                raise HTTPException(status_code=500, detail="Failed to create any floor plans")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating default floor plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create default floor plan: {str(e)}")


@router.get("/assistant/state")
async def get_assistant_state_frontend(db: AsyncSession = Depends(get_db)):
    """Get assistant state in frontend-compatible format."""
    try:
        # Get assistant from database
        stmt = select(AssistantState).filter(AssistantState.id == "default")
        result = await db.execute(stmt)
        assistant = result.scalar_one_or_none()

        if not assistant:
            # Return default state if no assistant found
            return {
                "position": {"x": 32, "y": 8},
                "room_id": "default",
                "floor_plan_id": "default",
                "facing": "up",
                "is_moving": False,
                "mood": "neutral",
                "expression": "default"
            }

        # Format in frontend-compatible structure
        return {
            "position": {
                "x": assistant.position_x,
                "y": assistant.position_y
            },
            "room_id": assistant.current_room_id,
            "floor_plan_id": assistant.current_floor_plan_id,
            "facing": assistant.facing_direction,
            "is_moving": assistant.is_moving,
            "mood": assistant.mood,
            "expression": assistant.expression
        }

    except Exception as e:
        logger.error(f"Error getting assistant state for frontend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get assistant state: {str(e)}")


@router.post("/assistant/position/sync")
async def sync_assistant_to_floor_plan(db: AsyncSession = Depends(get_db)):
    """Sync assistant position to match the modern house floor plan with pixel coordinates."""
    try:
        # Get the assistant
        stmt = select(AssistantState).filter(AssistantState.id == "default")
        result = await db.execute(stmt)
        assistant = result.scalar_one_or_none()

        if not assistant:
            assistant = AssistantState(id="default")
            db.add(assistant)

        # Manually sync to Modern House coordinates (pixel-based)
        # Position in center of living room: bounds (250, 300, 500, 400)
        center_x = 250 + (500 / 2)  # 500 pixels
        center_y = 300 + (400 / 2)  # 500 pixels

        # Update assistant state to match modern house
        assistant.current_floor_plan_id = "modern_house"
        assistant.current_room_id = "living_room"
        assistant.position_x = center_x
        assistant.position_y = center_y
        assistant.is_moving = False
        assistant.target_x = None
        assistant.target_y = None
        assistant.target_room_id = None
        assistant.movement_path = None

        await db.commit()

        return {
            "success": True,
            "message": "Assistant synced to Modern House with pixel coordinates",
            "floor_plan_id": "modern_house",
            "floor_plan_name": "Modern House",
            "room_id": "living_room",
            "room_name": "Living Room",
            "position": {
                "x": center_x,
                "y": center_y
            },
            "coordinate_system": "pixels"
        }

    except Exception as e:
        logger.error(f"Error syncing assistant position: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync assistant: {str(e)}")