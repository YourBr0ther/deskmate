"""
Action Executor Service for DeskMate.

This service handles the execution of actions decided by the Brain Council,
including movement, object interaction, state changes, and more complex
multi-step actions.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from app.services.assistant_service import assistant_service
from app.services.room_service import room_service
from app.services.multi_room_pathfinding import multi_room_pathfinding_service

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Execute actions decided by the Brain Council."""

    async def execute_actions(
        self,
        actions: List[Dict[str, Any]],
        broadcast_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a list of actions sequentially.

        Args:
            actions: List of action dictionaries from Brain Council
            broadcast_callback: Optional callback to broadcast state updates

        Returns:
            Execution results with success status and details
        """
        results = {
            "total_actions": len(actions),
            "executed": 0,
            "failed": 0,
            "action_results": []
        }

        for action in actions:
            try:
                result = await self.execute_single_action(action, broadcast_callback)
                results["action_results"].append(result)

                if result["success"]:
                    results["executed"] += 1
                else:
                    results["failed"] += 1

                # Small delay between actions for visual clarity
                await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(f"Error executing action {action}: {e}")
                results["failed"] += 1
                results["action_results"].append({
                    "action": action,
                    "success": False,
                    "error": str(e)
                })

        return results

    async def execute_single_action(
        self,
        action: Dict[str, Any],
        broadcast_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute a single action."""
        action_type = action.get("type", "unknown")
        target = action.get("target")
        parameters = action.get("parameters", {})

        logger.info(f"Executing action: type={action_type}, target={target}")

        # Route to appropriate handler
        if action_type == "move":
            return await self._execute_move(target, parameters, broadcast_callback)
        elif action_type == "interact":
            return await self._execute_interact(target, parameters, broadcast_callback)
        elif action_type == "state_change":
            return await self._execute_state_change(target, parameters, broadcast_callback)
        elif action_type == "pick_up":
            return await self._execute_pick_up(target, parameters, broadcast_callback)
        elif action_type == "put_down":
            return await self._execute_put_down(target, parameters, broadcast_callback)
        elif action_type == "expression":
            return await self._execute_expression(target, parameters, broadcast_callback)
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return {
                "action": action,
                "success": False,
                "error": f"Unknown action type: {action_type}"
            }

    async def _execute_move(
        self,
        target: Any,
        parameters: Dict[str, Any],
        broadcast_callback: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute movement action."""
        try:
            # Parse target coordinates
            x, y = self._parse_coordinates(target)
            if x is None or y is None:
                return {
                    "action": "move",
                    "success": False,
                    "error": f"Invalid target coordinates: {target}"
                }

            # Get current position
            assistant_state = await assistant_service.get_assistant_state()
            start_x = assistant_state.position_x
            start_y = assistant_state.position_y

            # Check if already at target
            if start_x == x and start_y == y:
                logger.info(f"Assistant already at target position ({x}, {y})")
                return {
                    "action": "move",
                    "success": True,
                    "message": "Already at target position"
                }

            # Get obstacles from room objects
            objects = await room_service.get_all_objects()
            obstacles = set()
            for obj in objects:
                if obj.get("properties", {}).get("solid", False):
                    obj_x = obj.get("position", {}).get("x", 0)
                    obj_y = obj.get("position", {}).get("y", 0)
                    width = obj.get("size", {}).get("width", 1)
                    height = obj.get("size", {}).get("height", 1)

                    # Add all cells occupied by the object as obstacles
                    for dx in range(width):
                        for dy in range(height):
                            obstacles.add((obj_x + dx, obj_y + dy))

            # Calculate path using multi-room pathfinding (single room mode)
            # For now, use the studio apartment default room
            from sqlalchemy.ext.asyncio import AsyncSession
            from app.database import get_db

            # Get DB session
            async for db in get_db():
                path_result = multi_room_pathfinding_service.find_multi_room_path(
                    db=db,
                    floor_plan_id="studio_apartment",
                    start_pos=(float(start_x), float(start_y)),
                    start_room_id="main_room",
                    goal_pos=(float(x), float(y)),
                    goal_room_id="main_room"
                )
                path = path_result.get("path", [])
                break

            if not path:
                return {
                    "action": "move",
                    "success": False,
                    "error": f"No path found to ({x}, {y})"
                }

            # Execute movement along path (extract coordinates from PathPoint objects)
            for i, point in enumerate(path[1:], 1):  # Skip starting position
                px, py = point.x if hasattr(point, 'x') else point[0], point.y if hasattr(point, 'y') else point[1]
                # Update position
                await assistant_service.update_assistant_position(
                    px, py,
                    facing=self._calculate_facing(
                        (path[i-1].x if hasattr(path[i-1], 'x') else path[i-1][0],
                         path[i-1].y if hasattr(path[i-1], 'y') else path[i-1][1]),
                        (px, py)
                    ),
                    action="walking"
                )

                # Broadcast update if callback provided
                if broadcast_callback:
                    state = await assistant_service.get_assistant_state()
                    await broadcast_callback({
                        "type": "assistant_state",
                        "data": state.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    })

                # Animation delay
                await asyncio.sleep(0.1)

            # Set to idle at destination
            await assistant_service.update_assistant_position(
                x, y,
                action="idle"
            )

            if broadcast_callback:
                state = await assistant_service.get_assistant_state()
                await broadcast_callback({
                    "type": "assistant_state",
                    "data": state.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })

            return {
                "action": "move",
                "success": True,
                "from": {"x": start_x, "y": start_y},
                "to": {"x": x, "y": y},
                "path_length": len(path)
            }

        except Exception as e:
            logger.error(f"Move execution error: {e}")
            return {
                "action": "move",
                "success": False,
                "error": str(e)
            }

    async def _execute_interact(
        self,
        target: str,
        parameters: Dict[str, Any],
        broadcast_callback: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute object interaction."""
        try:
            if not target:
                return {
                    "action": "interact",
                    "success": False,
                    "error": "No target object specified"
                }

            # Get object
            objects = await room_service.get_all_objects()
            target_obj = next((obj for obj in objects if obj["id"] == target), None)

            if not target_obj:
                return {
                    "action": "interact",
                    "success": False,
                    "error": f"Object not found: {target}"
                }

            # Get interaction type
            interaction_type = parameters.get("interaction", "activate")

            # Check if assistant is close enough
            assistant_state = await assistant_service.get_assistant_state()
            distance = self._calculate_distance(
                (assistant_state.position_x, assistant_state.position_y),
                (target_obj.get("position", {}).get("x", 0),
                 target_obj.get("position", {}).get("y", 0))
            )

            if distance > 2:  # Must be within 2 cells to interact
                return {
                    "action": "interact",
                    "success": False,
                    "error": f"Too far from {target_obj['name']} (distance: {distance})"
                }

            # Execute interaction based on type
            if interaction_type == "activate":
                # Toggle object state
                current_states = await room_service.get_object_states(target)

                if "power" in current_states:
                    new_state = "off" if current_states["power"] == "on" else "on"
                    await room_service.set_object_state(target, "power", new_state, "assistant")
                    message = f"Turned {target_obj['name']} {new_state}"
                elif "open" in current_states:
                    new_state = "closed" if current_states["open"] == "open" else "open"
                    await room_service.set_object_state(target, "open", new_state, "assistant")
                    message = f"{new_state.capitalize()} {target_obj['name']}"
                elif "active" in current_states:
                    new_state = "inactive" if current_states["active"] == "active" else "active"
                    await room_service.set_object_state(target, "active", new_state, "assistant")
                    message = f"Set {target_obj['name']} to {new_state}"
                else:
                    # Default interaction
                    await room_service.set_object_state(target, "interacted", "true", "assistant")
                    message = f"Interacted with {target_obj['name']}"

            elif interaction_type == "examine":
                message = f"Examined {target_obj['name']}"

            elif interaction_type == "use":
                message = f"Used {target_obj['name']}"

            else:
                message = f"Performed {interaction_type} on {target_obj['name']}"

            # Broadcast room update if states changed
            if broadcast_callback and interaction_type == "activate":
                await broadcast_callback({
                    "type": "room_update",
                    "data": {
                        "object_id": target,
                        "states": await room_service.get_object_states(target)
                    },
                    "timestamp": datetime.now().isoformat()
                })

            return {
                "action": "interact",
                "success": True,
                "object": target_obj["name"],
                "interaction": interaction_type,
                "message": message
            }

        except Exception as e:
            logger.error(f"Interact execution error: {e}")
            return {
                "action": "interact",
                "success": False,
                "error": str(e)
            }

    async def _execute_state_change(
        self,
        target: str,
        parameters: Dict[str, Any],
        broadcast_callback: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute state change action."""
        try:
            state_key = parameters.get("state_key")
            state_value = parameters.get("state_value")

            if not target or not state_key or not state_value:
                return {
                    "action": "state_change",
                    "success": False,
                    "error": "Missing required parameters"
                }

            # Apply state change
            await room_service.set_object_state(target, state_key, state_value, "assistant")

            # Broadcast update
            if broadcast_callback:
                await broadcast_callback({
                    "type": "room_update",
                    "data": {
                        "object_id": target,
                        "states": await room_service.get_object_states(target)
                    },
                    "timestamp": datetime.now().isoformat()
                })

            return {
                "action": "state_change",
                "success": True,
                "object": target,
                "state": {state_key: state_value}
            }

        except Exception as e:
            logger.error(f"State change execution error: {e}")
            return {
                "action": "state_change",
                "success": False,
                "error": str(e)
            }

    async def _execute_pick_up(
        self,
        target: str,
        parameters: Dict[str, Any],
        broadcast_callback: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute pick up action."""
        try:
            if not target:
                return {
                    "action": "pick_up",
                    "success": False,
                    "error": "No target object specified"
                }

            # Check if object is pickable
            objects = await room_service.get_all_objects()
            target_obj = next((obj for obj in objects if obj["id"] == target), None)

            if not target_obj:
                return {
                    "action": "pick_up",
                    "success": False,
                    "error": f"Object not found: {target}"
                }

            if not target_obj.get("properties", {}).get("movable", False):
                return {
                    "action": "pick_up",
                    "success": False,
                    "error": f"{target_obj['name']} cannot be picked up"
                }

            # Check if assistant is close enough to pick up
            assistant_state = await assistant_service.get_assistant_state()
            distance = self._calculate_distance(
                (assistant_state.position_x, assistant_state.position_y),
                (target_obj.get("position", {}).get("x", 0),
                 target_obj.get("position", {}).get("y", 0))
            )

            if distance > 2:  # Must be within 2 cells to pick up
                return {
                    "action": "pick_up",
                    "success": False,
                    "error": f"Too far from {target_obj['name']} (distance: {distance}). Move closer first."
                }

            # Check if already holding something
            if assistant_state.holding_object_id:
                return {
                    "action": "pick_up",
                    "success": False,
                    "error": f"Already holding an object. Put it down first."
                }

            # Update assistant state to hold object
            assistant_state.holding_object_id = target

            # Save the updated state to database
            await assistant_service.update_assistant_state(assistant_state)

            # Broadcast update
            if broadcast_callback:
                await broadcast_callback({
                    "type": "assistant_state",
                    "data": assistant_state.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })

            return {
                "action": "pick_up",
                "success": True,
                "object": target_obj["name"],
                "message": f"Picked up {target_obj['name']}"
            }

        except Exception as e:
            logger.error(f"Pick up execution error: {e}")
            return {
                "action": "pick_up",
                "success": False,
                "error": str(e)
            }

    async def _execute_put_down(
        self,
        target: Any,
        parameters: Dict[str, Any],
        broadcast_callback: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute put down action."""
        try:
            assistant_state = await assistant_service.get_assistant_state()

            if not assistant_state.holding_object_id:
                return {
                    "action": "put_down",
                    "success": False,
                    "error": "Not holding any object"
                }

            # Get held object info
            objects = await room_service.get_all_objects()
            held_object = next((obj for obj in objects if obj["id"] == assistant_state.holding_object_id), None)

            if not held_object:
                return {
                    "action": "put_down",
                    "success": False,
                    "error": "Held object not found in room data"
                }

            # Determine target location
            target_x, target_y = None, None

            if target:
                # Specific location provided
                target_x, target_y = self._parse_coordinates(target)
                if target_x is None or target_y is None:
                    return {
                        "action": "put_down",
                        "success": False,
                        "error": f"Invalid target coordinates: {target}"
                    }
            else:
                # Default: place at assistant's current position
                target_x = assistant_state.position_x
                target_y = assistant_state.position_y

            # Validate target location is within grid bounds
            if target_x < 0 or target_x >= 64 or target_y < 0 or target_y >= 16:
                return {
                    "action": "put_down",
                    "success": False,
                    "error": f"Target location ({target_x}, {target_y}) is outside room boundaries"
                }

            # Check for collisions with other objects
            object_size = held_object.get("size", {"width": 1, "height": 1})
            collision_result = await self._check_object_collision(
                target_x, target_y,
                object_size["width"], object_size["height"],
                exclude_id=assistant_state.holding_object_id
            )

            if collision_result["has_collision"]:
                return {
                    "action": "put_down",
                    "success": False,
                    "error": f"Cannot place {held_object['name']} at ({target_x}, {target_y}): {collision_result['reason']}"
                }

            # Check distance from assistant (should be within reach)
            distance = self._calculate_distance(
                (assistant_state.position_x, assistant_state.position_y),
                (target_x, target_y)
            )

            if distance > 3:  # Allow slightly more range for putting down
                return {
                    "action": "put_down",
                    "success": False,
                    "error": f"Target location too far away (distance: {distance}). Move closer first."
                }

            # Execute the put down
            await room_service.move_object(
                assistant_state.holding_object_id,
                target_x, target_y
            )

            # Clear holding state
            held_object_id = assistant_state.holding_object_id
            assistant_state.holding_object_id = None

            # Save the updated state to database
            await assistant_service.update_assistant_state(assistant_state)

            # Broadcast updates
            if broadcast_callback:
                # Broadcast assistant state update
                await broadcast_callback({
                    "type": "assistant_state",
                    "data": assistant_state.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })

                # Broadcast room update for object position
                await broadcast_callback({
                    "type": "room_update",
                    "data": {
                        "object_id": held_object_id,
                        "position": {"x": target_x, "y": target_y}
                    },
                    "timestamp": datetime.now().isoformat()
                })

            return {
                "action": "put_down",
                "success": True,
                "object": held_object["name"],
                "location": {"x": target_x, "y": target_y},
                "message": f"Put down {held_object['name']} at ({target_x}, {target_y})"
            }

        except Exception as e:
            logger.error(f"Put down execution error: {e}")
            return {
                "action": "put_down",
                "success": False,
                "error": str(e)
            }

    async def _execute_expression(
        self,
        target: str,
        parameters: Dict[str, Any],
        broadcast_callback: Optional[Any]
    ) -> Dict[str, Any]:
        """Execute expression change."""
        try:
            expression = target or parameters.get("expression", "neutral")

            # Update assistant expression
            assistant_state = await assistant_service.get_assistant_state()
            assistant_state.expression = expression

            # Broadcast update
            if broadcast_callback:
                await broadcast_callback({
                    "type": "assistant_state",
                    "data": assistant_state.to_dict(),
                    "timestamp": datetime.now().isoformat()
                })

            return {
                "action": "expression",
                "success": True,
                "expression": expression,
                "message": f"Changed expression to {expression}"
            }

        except Exception as e:
            logger.error(f"Expression execution error: {e}")
            return {
                "action": "expression",
                "success": False,
                "error": str(e)
            }

    def _parse_coordinates(self, target: Any) -> Tuple[Optional[int], Optional[int]]:
        """Parse target coordinates from various formats."""
        try:
            if isinstance(target, dict):
                return target.get("x"), target.get("y")
            elif isinstance(target, (list, tuple)) and len(target) == 2:
                return int(target[0]), int(target[1])
            elif isinstance(target, str):
                # Handle "x,y" or "(x, y)" formats
                clean = target.strip("()").strip()
                if "," in clean:
                    parts = clean.split(",")
                    return int(parts[0].strip()), int(parts[1].strip())
            return None, None
        except (ValueError, TypeError):
            return None, None

    def _calculate_facing(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> str:
        """Calculate facing direction based on movement."""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]

        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "down" if dy > 0 else "up"

    def _calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    async def _check_object_collision(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        exclude_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if placing an object at given position would cause collisions.

        Args:
            x, y: Top-left position of object
            width, height: Size of object
            exclude_id: Object ID to exclude from collision check (e.g., object being moved)

        Returns:
            Dict with collision info: {"has_collision": bool, "reason": str, "colliding_objects": list}
        """
        try:
            # Get all objects in room
            objects = await room_service.get_all_objects()

            # Check each object for collision
            colliding_objects = []

            for obj in objects:
                # Skip the excluded object (usually the one being placed)
                if exclude_id and obj["id"] == exclude_id:
                    continue

                # Skip non-solid objects (they don't block placement)
                if not obj.get("properties", {}).get("solid", True):
                    continue

                # Get object position and size
                obj_x = obj.get("position", {}).get("x", 0)
                obj_y = obj.get("position", {}).get("y", 0)
                obj_width = obj.get("size", {}).get("width", 1)
                obj_height = obj.get("size", {}).get("height", 1)

                # Check for overlap using rectangle collision detection
                if (x < obj_x + obj_width and
                    x + width > obj_x and
                    y < obj_y + obj_height and
                    y + height > obj_y):

                    colliding_objects.append({
                        "id": obj["id"],
                        "name": obj["name"],
                        "position": {"x": obj_x, "y": obj_y},
                        "size": {"width": obj_width, "height": obj_height}
                    })

            # Check collision with assistant position (can't place object on assistant)
            assistant_state = await assistant_service.get_assistant_state()
            if (x <= assistant_state.position_x < x + width and
                y <= assistant_state.position_y < y + height):

                colliding_objects.append({
                    "id": "assistant",
                    "name": "Assistant",
                    "position": {"x": assistant_state.position_x, "y": assistant_state.position_y},
                    "size": {"width": 1, "height": 1}
                })

            if colliding_objects:
                collision_names = [obj["name"] for obj in colliding_objects]
                reason = f"would overlap with {', '.join(collision_names)}"
                return {
                    "has_collision": True,
                    "reason": reason,
                    "colliding_objects": colliding_objects
                }

            return {
                "has_collision": False,
                "reason": "no collisions detected",
                "colliding_objects": []
            }

        except Exception as e:
            logger.error(f"Collision check error: {e}")
            return {
                "has_collision": True,
                "reason": f"collision check failed: {str(e)}",
                "colliding_objects": []
            }


# Global instance
action_executor = ActionExecutor()