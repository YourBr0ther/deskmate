"""
Template loading service for floor plan management.

This service handles loading floor plan templates from JSON files,
managing template database operations, and providing template
discovery and validation functionality.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.rooms import FloorPlan, Room, Wall, Doorway, FurnitureItem
from app.models.assistant import AssistantState

logger = logging.getLogger(__name__)


class TemplateLoaderService:
    """Service for loading and managing floor plan templates."""

    def __init__(self, templates_directory: str = None):
        if templates_directory is None:
            # Use relative path that works in both development and Docker
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            templates_directory = os.path.join(base_dir, "templates", "floor_plans")
        self.templates_directory = Path(templates_directory)
        self.supported_extensions = ['.json']

    def discover_templates(self) -> List[Dict[str, Any]]:
        """
        Discover all available template files in the templates directory.

        Returns:
            List of template metadata dictionaries
        """
        templates = []

        if not self.templates_directory.exists():
            logger.warning(f"Templates directory does not exist: {self.templates_directory}")
            return templates

        for file_path in self.templates_directory.glob("*.json"):
            try:
                template_info = self._get_template_info(file_path)
                if template_info:
                    templates.append(template_info)
            except Exception as e:
                logger.error(f"Error reading template {file_path}: {e}")

        return sorted(templates, key=lambda x: x.get('name', ''))

    def _get_template_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract basic template information from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "id": data.get("id"),
                "name": data.get("name"),
                "description": data.get("description"),
                "category": data.get("category"),
                "dimensions": data.get("dimensions", {}),
                "room_count": len(data.get("rooms", [])),
                "furniture_count": len(data.get("furniture", [])),
                "is_template": data.get("metadata", {}).get("is_template", True)
            }
        except Exception as e:
            logger.error(f"Error parsing template file {file_path}: {e}")
            return None

    def load_template_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load complete template data from JSON file.

        Args:
            file_path: Path to template JSON file

        Returns:
            Complete template data dictionary or None if error
        """
        try:
            template_path = Path(file_path)
            if not template_path.is_absolute():
                template_path = self.templates_directory / template_path

            with open(template_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ['id', 'name', 'dimensions', 'rooms']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except Exception as e:
            logger.error(f"Error loading template from {file_path}: {e}")
            return None

    async def load_template_to_database(self, db: AsyncSession, template_data: Dict[str, Any]) -> bool:
        """
        Load template data into database, creating all related objects.

        Args:
            db: Database session
            template_data: Complete template data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if template already exists
            stmt = select(FloorPlan).filter(FloorPlan.id == template_data["id"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                logger.info(f"Template {template_data['id']} already exists, skipping")
                return True

            # Create floor plan
            floor_plan = FloorPlan(
                id=template_data["id"],
                name=template_data["name"],
                description=template_data.get("description"),
                category=template_data.get("category", "unknown"),
                width=template_data["dimensions"]["width"],
                height=template_data["dimensions"]["height"],
                scale=template_data["dimensions"].get("scale", 1.0),
                units=template_data["dimensions"].get("units", "pixels"),
                background_color=template_data.get("styling", {}).get("background_color", "#f5f5f5"),
                wall_color=template_data.get("styling", {}).get("wall_color", "#333333"),
                wall_thickness=template_data.get("styling", {}).get("wall_thickness", 8),
                created_by=template_data.get("metadata", {}).get("created_by", "system"),
                is_template=template_data.get("metadata", {}).get("is_template", True),
                version=template_data.get("metadata", {}).get("version", "1.0")
            )
            db.add(floor_plan)
            db.flush()  # Get the ID

            # Create rooms
            for room_data in template_data.get("rooms", []):
                room = Room(
                    id=room_data["id"],
                    floor_plan_id=floor_plan.id,
                    name=room_data["name"],
                    room_type=room_data["type"],
                    bounds_x=room_data["bounds"]["x"],
                    bounds_y=room_data["bounds"]["y"],
                    bounds_width=room_data["bounds"]["width"],
                    bounds_height=room_data["bounds"]["height"],
                    floor_color=room_data["properties"]["floor_color"],
                    floor_material=room_data["properties"]["floor_material"],
                    lighting_level=room_data["properties"]["lighting_level"],
                    temperature=room_data["properties"]["temperature"],
                    is_accessible=room_data.get("accessibility", {}).get("is_accessible", True)
                )
                db.add(room)

            # Create walls
            for wall_data in template_data.get("walls", []):
                wall = Wall(
                    id=wall_data["id"],
                    floor_plan_id=floor_plan.id,
                    name=wall_data.get("name"),
                    start_x=wall_data["geometry"]["start"]["x"],
                    start_y=wall_data["geometry"]["start"]["y"],
                    end_x=wall_data["geometry"]["end"]["x"],
                    end_y=wall_data["geometry"]["end"]["y"],
                    wall_type=wall_data["properties"]["type"],
                    thickness=wall_data["properties"]["thickness"],
                    material=wall_data["properties"]["material"],
                    color=wall_data["properties"]["color"],
                    is_load_bearing=wall_data.get("structural", {}).get("is_load_bearing", False),
                    can_have_doorways=wall_data.get("structural", {}).get("can_have_doorways", True)
                )
                db.add(wall)

            # Create doorways
            for doorway_data in template_data.get("doorways", []):
                doorway = Doorway(
                    id=doorway_data["id"],
                    floor_plan_id=floor_plan.id,
                    wall_id=doorway_data["wall_id"],
                    name=doorway_data.get("name"),
                    position_on_wall=doorway_data["position"]["position_on_wall"],
                    width=doorway_data["position"]["width"],
                    room_a_id=doorway_data["connections"]["room_a"],
                    room_b_id=doorway_data["connections"]["room_b"],
                    doorway_type=doorway_data["properties"]["type"],
                    has_door=doorway_data["properties"].get("has_door", False),
                    door_state=doorway_data["properties"].get("door_state", "open"),
                    is_accessible=doorway_data.get("accessibility", {}).get("is_accessible", True),
                    requires_interaction=doorway_data.get("accessibility", {}).get("requires_interaction", False)
                )
                db.add(doorway)

            # Create furniture
            for furniture_data in template_data.get("furniture", []):
                furniture = FurnitureItem(
                    id=furniture_data["id"],
                    floor_plan_id=floor_plan.id,
                    room_id=furniture_data.get("room_id"),
                    name=furniture_data["name"],
                    description=furniture_data.get("description"),
                    furniture_type=furniture_data["type"],
                    position_x=furniture_data["position"]["x"],
                    position_y=furniture_data["position"]["y"],
                    rotation=furniture_data["position"].get("rotation", 0.0),
                    width=furniture_data["geometry"]["width"],
                    height=furniture_data["geometry"]["height"],
                    shape=furniture_data["geometry"].get("shape", "rectangle"),
                    is_solid=furniture_data["properties"]["solid"],
                    is_interactive=furniture_data["properties"]["interactive"],
                    is_movable=furniture_data["properties"].get("movable", False),
                    color_scheme=furniture_data["visual"]["color"],
                    material=furniture_data["visual"]["material"],
                    style=furniture_data["visual"]["style"],
                    can_sit_on=furniture_data["functional"]["can_sit_on"],
                    can_place_items_on=furniture_data["functional"]["can_place_items_on"],
                    storage_capacity=furniture_data["functional"]["storage_capacity"]
                )
                db.add(furniture)

            await db.commit()
            logger.info(f"Successfully loaded template {template_data['id']} to database")
            return True

        except Exception as e:
            logger.error(f"Error loading template to database: {e}")
            await db.rollback()
            return False

    async def load_all_templates(self, db: AsyncSession) -> Dict[str, bool]:
        """
        Load all discovered templates to database.

        Args:
            db: Database session

        Returns:
            Dictionary mapping template IDs to success status
        """
        results = {}
        templates = self.discover_templates()

        for template_info in templates:
            try:
                template_data = self.load_template_from_file(template_info["file_path"])
                if template_data:
                    success = await self.load_template_to_database(db, template_data)
                    results[template_data["id"]] = success
                else:
                    results[template_info["id"]] = False
            except Exception as e:
                logger.error(f"Error processing template {template_info.get('id', 'unknown')}: {e}")
                results[template_info.get("id", "unknown")] = False

        return results

    async def get_template_by_id(self, db: AsyncSession, template_id: str) -> Optional[FloorPlan]:
        """Get template floor plan by ID."""
        stmt = select(FloorPlan).filter(
            FloorPlan.id == template_id,
            FloorPlan.is_template == True
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def activate_template(self, db: AsyncSession, template_id: str, assistant_id: str = "default") -> Dict[str, Any]:
        """
        Activate a template as the current floor plan and position assistant.

        Args:
            db: Database session
            template_id: Template ID to activate
            assistant_id: Assistant to position

        Returns:
            Result dictionary with success status and details
        """
        try:
            # Get template
            template = await self.get_template_by_id(db, template_id)
            if not template:
                return {"success": False, "error": f"Template {template_id} not found"}

            # Deactivate all current floor plans
            stmt = select(FloorPlan)
            result = await db.execute(stmt)
            floor_plans = result.scalars().all()
            for fp in floor_plans:
                fp.is_active = False

            # Activate template
            template.is_active = True

            # Get first room for default positioning
            stmt = select(Room).filter(Room.floor_plan_id == template_id).limit(1)
            result = await db.execute(stmt)
            first_room = result.scalar_one_or_none()
            if not first_room:
                return {"success": False, "error": f"Template {template_id} has no rooms"}

            # Get or create assistant
            stmt = select(AssistantState).filter(AssistantState.id == assistant_id)
            result = await db.execute(stmt)
            assistant = result.scalar_one_or_none()
            if not assistant:
                assistant = AssistantState(id=assistant_id)
                db.add(assistant)

            # Position assistant in center of first room
            center_x = first_room.bounds_x + first_room.bounds_width / 2
            center_y = first_room.bounds_y + first_room.bounds_height / 2

            assistant.current_floor_plan_id = template_id
            assistant.current_room_id = first_room.id
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
                "template_id": template_id,
                "template_name": template.name,
                "default_room": first_room.id,
                "default_position": {"x": center_x, "y": center_y},
                "assistant_id": assistant_id
            }

        except Exception as e:
            logger.error(f"Error activating template {template_id}: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    def validate_template_data(self, template_data: Dict[str, Any]) -> List[str]:
        """
        Validate template data structure and return list of errors.

        Args:
            template_data: Template data to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required top-level fields
        required_fields = ["id", "name", "dimensions", "rooms"]
        for field in required_fields:
            if field not in template_data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        # Validate dimensions
        dimensions = template_data["dimensions"]
        if not isinstance(dimensions.get("width"), (int, float)) or dimensions["width"] <= 0:
            errors.append("Invalid dimensions.width")
        if not isinstance(dimensions.get("height"), (int, float)) or dimensions["height"] <= 0:
            errors.append("Invalid dimensions.height")

        # Validate rooms
        rooms = template_data["rooms"]
        if not isinstance(rooms, list) or len(rooms) == 0:
            errors.append("Template must have at least one room")

        room_ids = set()
        for i, room in enumerate(rooms):
            room_errors = self._validate_room(room, i)
            errors.extend(room_errors)

            if "id" in room:
                if room["id"] in room_ids:
                    errors.append(f"Duplicate room ID: {room['id']}")
                room_ids.add(room["id"])

        # Validate doorways reference valid rooms
        for i, doorway in enumerate(template_data.get("doorways", [])):
            if "connections" in doorway:
                room_a = doorway["connections"].get("room_a")
                room_b = doorway["connections"].get("room_b")
                if room_a not in room_ids:
                    errors.append(f"Doorway {i} references unknown room_a: {room_a}")
                if room_b not in room_ids:
                    errors.append(f"Doorway {i} references unknown room_b: {room_b}")

        return errors

    def _validate_room(self, room: Dict[str, Any], index: int) -> List[str]:
        """Validate individual room data."""
        errors = []
        prefix = f"Room {index}"

        required_fields = ["id", "name", "type", "bounds", "properties"]
        for field in required_fields:
            if field not in room:
                errors.append(f"{prefix}: Missing required field {field}")

        if "bounds" in room:
            bounds = room["bounds"]
            for coord in ["x", "y", "width", "height"]:
                if not isinstance(bounds.get(coord), (int, float)) or bounds[coord] < 0:
                    errors.append(f"{prefix}: Invalid bounds.{coord}")

        return errors


# Global service instance
template_loader_service = TemplateLoaderService()