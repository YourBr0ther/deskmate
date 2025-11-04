"""
Coordinate migration utilities for converting from grid-based to continuous coordinates.

This module provides utilities to migrate existing DeskMate data from the
old 64x16 grid system to the new continuous pixel-based coordinate system.
"""

from typing import Dict, Any, Tuple, List, Optional
import math


class CoordinateMigrationUtils:
    """
    Utilities for converting between grid and continuous coordinate systems.
    """

    # Old grid system constants
    OLD_GRID_WIDTH = 64
    OLD_GRID_HEIGHT = 16
    OLD_CELL_WIDTH = 20  # pixels
    OLD_CELL_HEIGHT = 30  # pixels

    # New coordinate system constants (for studio apartment template)
    DEFAULT_FLOOR_PLAN_WIDTH = 1300
    DEFAULT_FLOOR_PLAN_HEIGHT = 600
    DEFAULT_ROOM_BOUNDS = {"x": 50, "y": 50, "width": 1200, "height": 500}

    @classmethod
    def grid_to_continuous(cls, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """
        Convert grid coordinates to continuous pixel coordinates.

        Args:
            grid_x: Grid X coordinate (0-63)
            grid_y: Grid Y coordinate (0-15)

        Returns:
            Tuple of (pixel_x, pixel_y) in continuous coordinate system
        """
        # Convert grid position to old pixel position
        old_pixel_x = grid_x * cls.OLD_CELL_WIDTH
        old_pixel_y = grid_y * cls.OLD_CELL_HEIGHT

        # Map old pixel system (1280x480) to new system (1300x600)
        # Add offset for room bounds and scale proportionally
        scale_x = cls.DEFAULT_ROOM_BOUNDS["width"] / (cls.OLD_GRID_WIDTH * cls.OLD_CELL_WIDTH)
        scale_y = cls.DEFAULT_ROOM_BOUNDS["height"] / (cls.OLD_GRID_HEIGHT * cls.OLD_CELL_HEIGHT)

        new_x = cls.DEFAULT_ROOM_BOUNDS["x"] + (old_pixel_x * scale_x)
        new_y = cls.DEFAULT_ROOM_BOUNDS["y"] + (old_pixel_y * scale_y)

        return (new_x, new_y)

    @classmethod
    def continuous_to_grid(cls, pixel_x: float, pixel_y: float) -> Tuple[int, int]:
        """
        Convert continuous coordinates back to grid coordinates (for backward compatibility).

        Args:
            pixel_x: Continuous X coordinate
            pixel_y: Continuous Y coordinate

        Returns:
            Tuple of (grid_x, grid_y)
        """
        # Remove room offset
        relative_x = pixel_x - cls.DEFAULT_ROOM_BOUNDS["x"]
        relative_y = pixel_y - cls.DEFAULT_ROOM_BOUNDS["y"]

        # Scale back to old system
        scale_x = (cls.OLD_GRID_WIDTH * cls.OLD_CELL_WIDTH) / cls.DEFAULT_ROOM_BOUNDS["width"]
        scale_y = (cls.OLD_GRID_HEIGHT * cls.OLD_CELL_HEIGHT) / cls.DEFAULT_ROOM_BOUNDS["height"]

        old_pixel_x = relative_x * scale_x
        old_pixel_y = relative_y * scale_y

        # Convert to grid coordinates
        grid_x = int(old_pixel_x / cls.OLD_CELL_WIDTH)
        grid_y = int(old_pixel_y / cls.OLD_CELL_HEIGHT)

        # Clamp to valid grid bounds
        grid_x = max(0, min(cls.OLD_GRID_WIDTH - 1, grid_x))
        grid_y = max(0, min(cls.OLD_GRID_HEIGHT - 1, grid_y))

        return (grid_x, grid_y)

    @classmethod
    def migrate_assistant_position(cls, assistant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate assistant position data from grid to continuous coordinates.

        Args:
            assistant_data: Dictionary containing assistant state

        Returns:
            Updated dictionary with continuous coordinates
        """
        migrated_data = assistant_data.copy()

        # Convert position
        if "position_x" in assistant_data and "position_y" in assistant_data:
            grid_x = assistant_data["position_x"]
            grid_y = assistant_data["position_y"]
            new_x, new_y = cls.grid_to_continuous(grid_x, grid_y)

            migrated_data.update({
                "position_x": new_x,
                "position_y": new_y,
                "current_floor_plan_id": "studio_apartment",
                "current_room_id": "studio_main"
            })

        # Convert target position if moving
        if "target_x" in assistant_data and "target_y" in assistant_data:
            if assistant_data["target_x"] is not None and assistant_data["target_y"] is not None:
                target_x, target_y = cls.grid_to_continuous(
                    assistant_data["target_x"],
                    assistant_data["target_y"]
                )
                migrated_data.update({
                    "target_x": target_x,
                    "target_y": target_y,
                    "target_room_id": "studio_main"
                })

        # Convert movement path
        if "movement_path" in assistant_data and assistant_data["movement_path"]:
            new_path = []
            for point in assistant_data["movement_path"]:
                if isinstance(point, dict) and "x" in point and "y" in point:
                    new_x, new_y = cls.grid_to_continuous(point["x"], point["y"])
                    new_path.append({"x": new_x, "y": new_y})
                elif isinstance(point, (list, tuple)) and len(point) >= 2:
                    new_x, new_y = cls.grid_to_continuous(point[0], point[1])
                    new_path.append({"x": new_x, "y": new_y})

            migrated_data["movement_path"] = new_path

        # Update movement speed from cells/second to pixels/second
        if "movement_speed" in assistant_data:
            old_speed = assistant_data["movement_speed"]  # cells per second
            # Convert to pixels per second (approximate)
            new_speed = old_speed * 25  # 25 pixels per cell equivalent
            migrated_data["movement_speed"] = new_speed

        return migrated_data

    @classmethod
    def migrate_object_position(cls, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate object position data from grid to continuous coordinates.

        Args:
            object_data: Dictionary containing object state

        Returns:
            Updated dictionary with continuous coordinates
        """
        migrated_data = object_data.copy()

        # Convert position
        if "position_x" in object_data and "position_y" in object_data:
            grid_x = object_data["position_x"]
            grid_y = object_data["position_y"]
            new_x, new_y = cls.grid_to_continuous(grid_x, grid_y)

            migrated_data.update({
                "position_x": new_x,
                "position_y": new_y,
                "floor_plan_id": "studio_apartment",
                "room_id": "studio_main"
            })

        # Convert size from grid cells to pixels
        if "size_width" in object_data and "size_height" in object_data:
            grid_width = object_data["size_width"]
            grid_height = object_data["size_height"]

            # Convert grid cells to pixels
            pixel_width = grid_width * cls.OLD_CELL_WIDTH
            pixel_height = grid_height * cls.OLD_CELL_HEIGHT

            # Scale to new coordinate system
            scale_x = cls.DEFAULT_ROOM_BOUNDS["width"] / (cls.OLD_GRID_WIDTH * cls.OLD_CELL_WIDTH)
            scale_y = cls.DEFAULT_ROOM_BOUNDS["height"] / (cls.OLD_GRID_HEIGHT * cls.OLD_CELL_HEIGHT)

            migrated_data.update({
                "width": pixel_width * scale_x,
                "height": pixel_height * scale_y
            })

            # Remove old grid-based size fields
            migrated_data.pop("size_width", None)
            migrated_data.pop("size_height", None)

        return migrated_data

    @classmethod
    def create_default_studio_apartment(cls) -> Dict[str, Any]:
        """
        Create the default studio apartment floor plan for migration.

        Returns:
            Dictionary representing the studio apartment template
        """
        from .floor_plans import FloorPlanTemplateManager

        template = FloorPlanTemplateManager.get_studio_apartment()
        return FloorPlanTemplateManager.template_to_dict(template)

    @classmethod
    def migrate_room_layout(cls, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate room layout data from grid-based to floor plan system.

        Args:
            layout_data: Dictionary containing room layout data

        Returns:
            Updated dictionary with floor plan data
        """
        # For now, convert any existing room layout to studio apartment
        studio_template = cls.create_default_studio_apartment()

        # Preserve any custom settings if they exist
        if "background_color" in layout_data:
            studio_template["background_color"] = layout_data["background_color"]
        if "wall_positions" in layout_data:
            # Convert wall positions if needed (for now, use template walls)
            pass

        return studio_template

    @classmethod
    def validate_migration(cls, original_data: Dict[str, Any], migrated_data: Dict[str, Any]) -> List[str]:
        """
        Validate that migration was successful and data is consistent.

        Args:
            original_data: Original grid-based data
            migrated_data: Migrated continuous coordinate data

        Returns:
            List of validation errors (empty if successful)
        """
        errors = []

        # Check that essential fields are present
        if "position_x" in original_data:
            if "position_x" not in migrated_data:
                errors.append("Missing position_x in migrated data")
            elif not isinstance(migrated_data["position_x"], (int, float)):
                errors.append("Invalid position_x type in migrated data")

        if "position_y" in original_data:
            if "position_y" not in migrated_data:
                errors.append("Missing position_y in migrated data")
            elif not isinstance(migrated_data["position_y"], (int, float)):
                errors.append("Invalid position_y type in migrated data")

        # Check bounds
        if "position_x" in migrated_data and "position_y" in migrated_data:
            x, y = migrated_data["position_x"], migrated_data["position_y"]
            if not (cls.DEFAULT_ROOM_BOUNDS["x"] <= x <= cls.DEFAULT_ROOM_BOUNDS["x"] + cls.DEFAULT_ROOM_BOUNDS["width"]):
                errors.append(f"Position X {x} is outside room bounds")
            if not (cls.DEFAULT_ROOM_BOUNDS["y"] <= y <= cls.DEFAULT_ROOM_BOUNDS["y"] + cls.DEFAULT_ROOM_BOUNDS["height"]):
                errors.append(f"Position Y {y} is outside room bounds")

        return errors

    @classmethod
    def get_migration_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of the migration process and coordinate system changes.

        Returns:
            Dictionary with migration information
        """
        return {
            "old_system": {
                "type": "grid",
                "grid_size": {"width": cls.OLD_GRID_WIDTH, "height": cls.OLD_GRID_HEIGHT},
                "cell_size": {"width": cls.OLD_CELL_WIDTH, "height": cls.OLD_CELL_HEIGHT},
                "total_size": {
                    "width": cls.OLD_GRID_WIDTH * cls.OLD_CELL_WIDTH,
                    "height": cls.OLD_GRID_HEIGHT * cls.OLD_CELL_HEIGHT
                }
            },
            "new_system": {
                "type": "continuous",
                "floor_plan_size": {"width": cls.DEFAULT_FLOOR_PLAN_WIDTH, "height": cls.DEFAULT_FLOOR_PLAN_HEIGHT},
                "room_bounds": cls.DEFAULT_ROOM_BOUNDS,
                "coordinate_units": "pixels"
            },
            "migration_notes": [
                "All positions converted from grid cells to continuous pixels",
                "Objects placed in default studio apartment floor plan",
                "Movement speed converted from cells/second to pixels/second",
                "Size measurements converted from grid cells to pixels",
                "Multi-room support added with default room assignments"
            ]
        }