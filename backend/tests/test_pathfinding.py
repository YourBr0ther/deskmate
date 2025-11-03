#!/usr/bin/env python3
"""
Test script for the pathfinding algorithm.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.pathfinding import PathfindingService

def test_basic_pathfinding():
    """Test basic pathfinding functionality."""
    pathfinder = PathfindingService(grid_width=10, grid_height=10)

    # Test simple straight line
    start = (0, 0)
    goal = (3, 0)
    obstacles = set()

    path = pathfinder.find_path(start, goal, obstacles)
    print(f"Simple path from {start} to {goal}: {path}")
    assert path == [(0, 0), (1, 0), (2, 0), (3, 0)], f"Expected straight path, got {path}"

def test_pathfinding_with_obstacles():
    """Test pathfinding around obstacles."""
    pathfinder = PathfindingService(grid_width=10, grid_height=10)

    # Create a wall blocking direct path
    start = (0, 2)
    goal = (5, 2)
    obstacles = {(2, 1), (2, 2), (2, 3)}  # Vertical wall

    path = pathfinder.find_path(start, goal, obstacles)
    print(f"Path around obstacle from {start} to {goal}: {path}")

    # Should go around the wall
    assert len(path) > 4, "Path should be longer than direct route due to obstacle"
    assert path[0] == start and path[-1] == goal, "Path should start and end correctly"

    # Verify no path goes through obstacles
    for pos in path:
        assert pos not in obstacles, f"Path goes through obstacle at {pos}"

def test_room_layout():
    """Test pathfinding in actual room layout."""
    pathfinder = PathfindingService(grid_width=64, grid_height=16)

    # Create obstacles based on room furniture
    obstacles = set()

    # Bed (50, 12) - 8x4
    for x in range(50, 58):
        for y in range(12, 16):
            obstacles.add((x, y))

    # Desk (10, 2) - 6x3
    for x in range(10, 16):
        for y in range(2, 5):
            obstacles.add((x, y))

    # Window (30, 0) - 8x1 (not solid, so not an obstacle)
    # Door (0, 8) - 1x3 (not solid, so not an obstacle)

    print(f"Room has {len(obstacles)} obstacle cells")

    # Test path from center to bed
    start = (32, 8)  # Center of room
    goal = (49, 14)  # Next to bed

    path = pathfinder.find_path(start, goal, obstacles)
    print(f"Path from center to bed: {path}")

    assert len(path) > 0, "Should find a path to bed area"
    assert path[0] == start and path[-1] == goal, "Path should start and end correctly"

    # Test unreachable position (inside bed)
    unreachable_goal = (52, 14)  # Inside bed
    no_path = pathfinder.find_path(start, unreachable_goal, obstacles)
    print(f"Path to unreachable position: {no_path}")
    assert len(no_path) == 0, "Should not find path to blocked position"

def visualize_path(path, obstacles, grid_width=10, grid_height=10):
    """Visualize a path on the grid."""
    print("\nGrid visualization:")
    for y in range(grid_height):
        row = ""
        for x in range(grid_width):
            if (x, y) in obstacles:
                row += "█"
            elif (x, y) in path:
                if (x, y) == path[0]:
                    row += "S"  # Start
                elif (x, y) == path[-1]:
                    row += "E"  # End
                else:
                    row += "·"  # Path
            else:
                row += " "
        print(row)

if __name__ == "__main__":
    print("Testing DeskMate Pathfinding Algorithm")
    print("=" * 40)

    test_basic_pathfinding()
    print("✅ Basic pathfinding test passed")

    test_pathfinding_with_obstacles()
    print("✅ Obstacle avoidance test passed")

    test_room_layout()
    print("✅ Room layout pathfinding test passed")

    # Demo visualization
    print("\nDemo: Path around obstacle")
    pathfinder = PathfindingService(grid_width=8, grid_height=6)
    start = (0, 2)
    goal = (7, 2)
    obstacles = {(3, 1), (3, 2), (3, 3), (4, 1), (4, 2), (4, 3)}
    path = pathfinder.find_path(start, goal, obstacles)
    visualize_path(path, obstacles, 8, 6)

    print("\n🎉 All pathfinding tests passed!")