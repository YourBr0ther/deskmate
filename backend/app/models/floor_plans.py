"""
Floor plan template definitions and management.

This module contains predefined floor plan templates and utilities
for loading, validating, and managing different room layouts.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class FloorPlanTemplate:
    """
    A floor plan template data structure.

    This represents the raw template data before it's converted
    to database models.
    """
    id: str
    name: str
    description: str
    category: str
    dimensions: Dict[str, Any]
    styling: Dict[str, Any]
    rooms: List[Dict[str, Any]]
    walls: List[Dict[str, Any]]
    doorways: List[Dict[str, Any]]
    furniture: List[Dict[str, Any]]


class FloorPlanTemplateManager:
    """
    Manages floor plan templates and provides utilities for
    loading, validating, and converting templates.
    """

    @staticmethod
    def get_studio_apartment() -> FloorPlanTemplate:
        """
        Studio apartment - single large room with defined areas.
        Optimized for 1344x1040 display area (70% of 1920x1080).
        """
        return FloorPlanTemplate(
            id="studio_apartment",
            name="Studio Apartment",
            description="Open floor plan studio with kitchen, living, and sleeping areas",
            category="apartment",
            dimensions={
                "width": 1300,
                "height": 600,
                "scale": 20,  # 20 pixels per foot
                "units": "feet"
            },
            styling={
                "background_color": "#f5f5f5",
                "background_image": None,
                "wall_color": "#333333",
                "wall_thickness": 8
            },
            rooms=[
                {
                    "id": "studio_main",
                    "name": "Studio",
                    "type": "studio",
                    "bounds": {"x": 50, "y": 50, "width": 1200, "height": 500},
                    "properties": {
                        "floor_color": "#e8e8e8",
                        "floor_material": "hardwood",
                        "lighting_level": 0.8,
                        "temperature": 72.0
                    }
                }
            ],
            walls=[
                # Exterior walls
                {"id": "wall_north", "start": [50, 50], "end": [1250, 50], "type": "exterior"},
                {"id": "wall_east", "start": [1250, 50], "end": [1250, 550], "type": "exterior"},
                {"id": "wall_south", "start": [1250, 550], "end": [50, 550], "type": "exterior"},
                {"id": "wall_west", "start": [50, 550], "end": [50, 50], "type": "exterior"},
                # Kitchen partition (half wall)
                {"id": "wall_kitchen", "start": [200, 100], "end": [400, 100], "type": "interior"}
            ],
            doorways=[
                {
                    "id": "door_entrance",
                    "wall_id": "wall_west",
                    "position_on_wall": 0.7,
                    "width": 80,
                    "connects": ["studio_main", "hallway"],
                    "type": "door"
                }
            ],
            furniture=[
                # Kitchen area
                {
                    "id": "kitchen_counter",
                    "name": "Kitchen Counter",
                    "type": "furniture",
                    "position": {"x": 80, "y": 80, "rotation": 0},
                    "size": {"width": 300, "height": 60},
                    "properties": {"solid": True, "interactive": True, "can_place_items_on": True},
                    "visual": {"color": "#8B4513", "material": "wood", "style": "modern"}
                },
                {
                    "id": "refrigerator",
                    "name": "Refrigerator",
                    "type": "appliance",
                    "position": {"x": 80, "y": 150, "rotation": 0},
                    "size": {"width": 60, "height": 60},
                    "properties": {"solid": True, "interactive": True},
                    "visual": {"color": "#C0C0C0", "material": "metal", "style": "modern"}
                },
                # Living area
                {
                    "id": "sofa",
                    "name": "Sofa",
                    "type": "furniture",
                    "position": {"x": 500, "y": 300, "rotation": 0},
                    "size": {"width": 180, "height": 80},
                    "properties": {"solid": True, "interactive": True, "can_sit_on": True},
                    "visual": {"color": "#4A4A4A", "material": "fabric", "style": "modern"}
                },
                {
                    "id": "coffee_table",
                    "name": "Coffee Table",
                    "type": "furniture",
                    "position": {"x": 550, "y": 400, "rotation": 0},
                    "size": {"width": 80, "height": 40},
                    "properties": {"solid": True, "interactive": True, "can_place_items_on": True},
                    "visual": {"color": "#8B4513", "material": "wood", "style": "modern"}
                },
                # Sleeping area
                {
                    "id": "bed",
                    "name": "Bed",
                    "type": "furniture",
                    "position": {"x": 900, "y": 350, "rotation": 0},
                    "size": {"width": 160, "height": 120},
                    "properties": {"solid": True, "interactive": True, "can_sit_on": True},
                    "visual": {"color": "#FFFFFF", "material": "fabric", "style": "modern"}
                },
                {
                    "id": "nightstand",
                    "name": "Nightstand",
                    "type": "furniture",
                    "position": {"x": 1070, "y": 370, "rotation": 0},
                    "size": {"width": 40, "height": 40},
                    "properties": {"solid": True, "interactive": True, "can_place_items_on": True},
                    "visual": {"color": "#8B4513", "material": "wood", "style": "modern"}
                }
            ]
        )

    @staticmethod
    def get_two_bedroom_apartment() -> FloorPlanTemplate:
        """
        Two bedroom apartment with separate rooms connected by doorways.
        """
        return FloorPlanTemplate(
            id="two_bedroom_apartment",
            name="Two Bedroom Apartment",
            description="Apartment with living room, kitchen, and two bedrooms",
            category="apartment",
            dimensions={
                "width": 1300,
                "height": 900,
                "scale": 20,
                "units": "feet"
            },
            styling={
                "background_color": "#f5f5f5",
                "wall_color": "#333333",
                "wall_thickness": 8
            },
            rooms=[
                {
                    "id": "living_room",
                    "name": "Living Room",
                    "type": "living_room",
                    "bounds": {"x": 50, "y": 50, "width": 600, "height": 400},
                    "properties": {"floor_material": "hardwood", "lighting_level": 0.8}
                },
                {
                    "id": "kitchen",
                    "name": "Kitchen",
                    "type": "kitchen",
                    "bounds": {"x": 700, "y": 50, "width": 300, "height": 200},
                    "properties": {"floor_material": "tile", "lighting_level": 0.9}
                },
                {
                    "id": "master_bedroom",
                    "name": "Master Bedroom",
                    "type": "bedroom",
                    "bounds": {"x": 50, "y": 500, "width": 400, "height": 350},
                    "properties": {"floor_material": "carpet", "lighting_level": 0.6}
                },
                {
                    "id": "second_bedroom",
                    "name": "Second Bedroom",
                    "type": "bedroom",
                    "bounds": {"x": 500, "y": 500, "width": 300, "height": 350},
                    "properties": {"floor_material": "carpet", "lighting_level": 0.6}
                },
                {
                    "id": "bathroom",
                    "name": "Bathroom",
                    "type": "bathroom",
                    "bounds": {"x": 850, "y": 500, "width": 150, "height": 200},
                    "properties": {"floor_material": "tile", "lighting_level": 0.9}
                }
            ],
            walls=[
                # Exterior walls
                {"id": "wall_north", "start": [50, 50], "end": [1000, 50], "type": "exterior"},
                {"id": "wall_east", "start": [1000, 50], "end": [1000, 850], "type": "exterior"},
                {"id": "wall_south", "start": [1000, 850], "end": [50, 850], "type": "exterior"},
                {"id": "wall_west", "start": [50, 850], "end": [50, 50], "type": "exterior"},

                # Interior walls
                {"id": "wall_kitchen_living", "start": [650, 50], "end": [650, 250], "type": "interior"},
                {"id": "wall_bedrooms_living", "start": [50, 450], "end": [800, 450], "type": "interior"},
                {"id": "wall_bedroom_divide", "start": [450, 450], "end": [450, 850], "type": "interior"},
                {"id": "wall_bathroom", "start": [800, 450], "end": [800, 700], "type": "interior"}
            ],
            doorways=[
                {
                    "id": "door_kitchen_living",
                    "wall_id": "wall_kitchen_living",
                    "position_on_wall": 0.8,
                    "width": 80,
                    "connects": ["living_room", "kitchen"],
                    "type": "open"
                },
                {
                    "id": "door_master_living",
                    "wall_id": "wall_bedrooms_living",
                    "position_on_wall": 0.3,
                    "width": 80,
                    "connects": ["living_room", "master_bedroom"],
                    "type": "door"
                },
                {
                    "id": "door_second_living",
                    "wall_id": "wall_bedrooms_living",
                    "position_on_wall": 0.7,
                    "width": 80,
                    "connects": ["living_room", "second_bedroom"],
                    "type": "door"
                }
            ],
            furniture=[
                # Living room furniture
                {
                    "id": "sectional_sofa",
                    "name": "Sectional Sofa",
                    "type": "furniture",
                    "position": {"x": 200, "y": 200, "rotation": 0},
                    "size": {"width": 200, "height": 120},
                    "properties": {"solid": True, "can_sit_on": True},
                    "visual": {"color": "#4A4A4A", "material": "fabric"}
                },
                {
                    "id": "tv_stand",
                    "name": "TV Stand",
                    "type": "furniture",
                    "position": {"x": 500, "y": 100, "rotation": 0},
                    "size": {"width": 120, "height": 40},
                    "properties": {"solid": True, "can_place_items_on": True},
                    "visual": {"color": "#2F2F2F", "material": "wood"}
                },

                # Kitchen furniture
                {
                    "id": "kitchen_island",
                    "name": "Kitchen Island",
                    "type": "furniture",
                    "position": {"x": 750, "y": 120, "rotation": 0},
                    "size": {"width": 150, "height": 60},
                    "properties": {"solid": True, "can_place_items_on": True},
                    "visual": {"color": "#8B4513", "material": "wood"}
                },

                # Master bedroom furniture
                {
                    "id": "master_bed",
                    "name": "Queen Bed",
                    "type": "furniture",
                    "position": {"x": 150, "y": 600, "rotation": 0},
                    "size": {"width": 160, "height": 120},
                    "properties": {"solid": True, "can_sit_on": True},
                    "visual": {"color": "#FFFFFF", "material": "fabric"}
                },

                # Second bedroom furniture
                {
                    "id": "second_bed",
                    "name": "Twin Bed",
                    "type": "furniture",
                    "position": {"x": 550, "y": 600, "rotation": 0},
                    "size": {"width": 120, "height": 80},
                    "properties": {"solid": True, "can_sit_on": True},
                    "visual": {"color": "#E6E6FA", "material": "fabric"}
                }
            ]
        )

    @staticmethod
    def get_office_building() -> FloorPlanTemplate:
        """
        Office building layout with multiple workspaces.
        """
        return FloorPlanTemplate(
            id="office_building",
            name="Office Building",
            description="Professional office space with meeting rooms and workstations",
            category="office",
            dimensions={
                "width": 1200,
                "height": 800,
                "scale": 20,
                "units": "feet"
            },
            styling={
                "background_color": "#f8f8f8",
                "wall_color": "#666666",
                "wall_thickness": 6
            },
            rooms=[
                {
                    "id": "main_office",
                    "name": "Main Office",
                    "type": "office",
                    "bounds": {"x": 50, "y": 50, "width": 700, "height": 400},
                    "properties": {"floor_material": "carpet", "lighting_level": 0.85}
                },
                {
                    "id": "conference_room",
                    "name": "Conference Room",
                    "type": "meeting",
                    "bounds": {"x": 800, "y": 50, "width": 300, "height": 200},
                    "properties": {"floor_material": "carpet", "lighting_level": 0.9}
                },
                {
                    "id": "break_room",
                    "name": "Break Room",
                    "type": "kitchen",
                    "bounds": {"x": 800, "y": 300, "width": 200, "height": 150},
                    "properties": {"floor_material": "tile", "lighting_level": 0.8}
                }
            ],
            walls=[
                # Exterior walls
                {"id": "wall_north", "start": [50, 50], "end": [1100, 50], "type": "exterior"},
                {"id": "wall_east", "start": [1100, 50], "end": [1100, 500], "type": "exterior"},
                {"id": "wall_south", "start": [1100, 500], "end": [50, 500], "type": "exterior"},
                {"id": "wall_west", "start": [50, 500], "end": [50, 50], "type": "exterior"},

                # Interior walls
                {"id": "wall_conference", "start": [750, 50], "end": [750, 250], "type": "interior"},
                {"id": "wall_break_room", "start": [750, 300], "end": [1000, 300], "type": "interior"}
            ],
            doorways=[
                {
                    "id": "door_conference",
                    "wall_id": "wall_conference",
                    "position_on_wall": 0.5,
                    "width": 80,
                    "connects": ["main_office", "conference_room"],
                    "type": "door"
                }
            ],
            furniture=[
                # Main office furniture
                {
                    "id": "desk_1",
                    "name": "Executive Desk",
                    "type": "furniture",
                    "position": {"x": 100, "y": 100, "rotation": 0},
                    "size": {"width": 120, "height": 60},
                    "properties": {"solid": True, "can_place_items_on": True},
                    "visual": {"color": "#8B4513", "material": "wood", "style": "professional"}
                },
                {
                    "id": "office_chair_1",
                    "name": "Office Chair",
                    "type": "furniture",
                    "position": {"x": 150, "y": 180, "rotation": 180},
                    "size": {"width": 50, "height": 50},
                    "properties": {"solid": False, "can_sit_on": True},
                    "visual": {"color": "#000000", "material": "leather", "style": "professional"}
                },

                # Conference room furniture
                {
                    "id": "conference_table",
                    "name": "Conference Table",
                    "type": "furniture",
                    "position": {"x": 850, "y": 100, "rotation": 0},
                    "size": {"width": 200, "height": 80},
                    "properties": {"solid": True, "can_place_items_on": True},
                    "visual": {"color": "#654321", "material": "wood", "style": "professional"}
                }
            ]
        )

    @staticmethod
    def get_all_templates() -> List[FloorPlanTemplate]:
        """Get all available floor plan templates."""
        return [
            FloorPlanTemplateManager.get_studio_apartment(),
            FloorPlanTemplateManager.get_two_bedroom_apartment(),
            FloorPlanTemplateManager.get_office_building()
        ]

    @staticmethod
    def get_template_by_id(template_id: str) -> Optional[FloorPlanTemplate]:
        """Get a specific template by ID."""
        templates = {
            "studio_apartment": FloorPlanTemplateManager.get_studio_apartment(),
            "two_bedroom_apartment": FloorPlanTemplateManager.get_two_bedroom_apartment(),
            "office_building": FloorPlanTemplateManager.get_office_building()
        }
        return templates.get(template_id)

    @staticmethod
    def validate_template(template: FloorPlanTemplate) -> List[str]:
        """
        Validate a floor plan template and return any errors.

        Returns:
            List of error messages, empty if template is valid.
        """
        errors = []

        # Check required fields
        if not template.id:
            errors.append("Template ID is required")
        if not template.name:
            errors.append("Template name is required")
        if not template.dimensions:
            errors.append("Template dimensions are required")

        # Check dimensions
        dims = template.dimensions
        if dims.get("width", 0) <= 0:
            errors.append("Template width must be positive")
        if dims.get("height", 0) <= 0:
            errors.append("Template height must be positive")

        # Check rooms
        if not template.rooms:
            errors.append("Template must have at least one room")

        room_ids = set()
        for room in template.rooms:
            if not room.get("id"):
                errors.append("Room ID is required")
            elif room["id"] in room_ids:
                errors.append(f"Duplicate room ID: {room['id']}")
            else:
                room_ids.add(room["id"])

        # Check doorway connections
        for doorway in template.doorways:
            connects = doorway.get("connects", [])
            for room_id in connects:
                if room_id not in room_ids and room_id != "hallway":  # Allow external connections
                    errors.append(f"Doorway references non-existent room: {room_id}")

        return errors

    @staticmethod
    def template_to_dict(template: FloorPlanTemplate) -> Dict[str, Any]:
        """Convert a template to a dictionary suitable for database storage."""
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "width": template.dimensions["width"],
            "height": template.dimensions["height"],
            "scale": template.dimensions.get("scale", 1.0),
            "units": template.dimensions.get("units", "feet"),
            "background_color": template.styling.get("background_color", "#f5f5f5"),
            "background_image": template.styling.get("background_image"),
            "wall_color": template.styling.get("wall_color", "#333333"),
            "wall_thickness": template.styling.get("wall_thickness", 8),
            "is_template": True,
            "version": "1.0"
        }


# Template registry for easy access
FLOOR_PLAN_TEMPLATES = {
    "studio_apartment": FloorPlanTemplateManager.get_studio_apartment(),
    "two_bedroom_apartment": FloorPlanTemplateManager.get_two_bedroom_apartment(),
    "office_building": FloorPlanTemplateManager.get_office_building()
}