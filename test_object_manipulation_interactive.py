#!/usr/bin/env python3
"""
Interactive Object Manipulation Test Script for Phase 8

This script provides an interactive way to test object manipulation features.
Run this script and use the menu to test different object manipulation scenarios.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

def print_banner():
    print("🧪 Phase 8 Object Manipulation Interactive Test")
    print("=" * 50)
    print()

def print_status(status: str, color: str = "blue"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['blue'])}{status}{colors['reset']}")

def make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make HTTP request and return response"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}

        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}

def get_assistant_state() -> Dict[str, Any]:
    """Get current assistant state"""
    result = make_request("GET", "/assistant/state")
    if result.get("success"):
        return result["data"]
    return {}

def get_holding_status() -> Dict[str, Any]:
    """Get what the assistant is currently holding"""
    result = make_request("GET", "/assistant/holding")
    if result.get("success"):
        return result["data"]
    return {}

def show_assistant_status():
    """Display current assistant status"""
    print_status("📍 Current Assistant Status:", "cyan")

    state = get_assistant_state()
    if state:
        pos = state.get("position", {})
        print(f"   Position: ({pos.get('x', '?')}, {pos.get('y', '?')})")
        print(f"   Action: {state.get('status', {}).get('action', 'unknown')}")
        print(f"   Mood: {state.get('status', {}).get('mood', 'unknown')}")

    holding = get_holding_status()
    if holding.get("holding_object_id"):
        print(f"   📦 Holding: {holding['holding_object_name']} ({holding['holding_object_id']})")
    else:
        print("   📦 Holding: Nothing")
    print()

def list_nearby_objects():
    """List objects near the assistant"""
    print_status("🔍 Objects in Room:", "cyan")

    result = make_request("GET", "/room/objects")
    if not result.get("success"):
        print_status("Failed to get room objects", "red")
        return

    assistant_state = get_assistant_state()
    assistant_pos = assistant_state.get("position", {})
    assistant_x, assistant_y = assistant_pos.get("x", 0), assistant_pos.get("y", 0)

    objects = result["data"]
    nearby_objects = []

    for obj in objects:
        obj_pos = obj.get("position", {})
        obj_x, obj_y = obj_pos.get("x", 0), obj_pos.get("y", 0)
        distance = abs(obj_x - assistant_x) + abs(obj_y - assistant_y)

        movable = obj.get("properties", {}).get("movable", False)
        status = "📦 MOVABLE" if movable else "🏠 FIXED"

        print(f"   {obj['name']} ({obj['id']}) - Distance: {distance} - {status}")

        if distance <= 2 and movable:
            nearby_objects.append(obj)

    print(f"\n   📋 {len(nearby_objects)} movable objects within reach")
    return nearby_objects

def test_pick_up():
    """Test picking up an object"""
    print_status("🎯 Pick Up Object Test", "yellow")

    nearby = list_nearby_objects()
    if not nearby:
        print_status("No movable objects within reach. Move closer to objects first.", "red")
        return

    print("\nAvailable objects to pick up:")
    for i, obj in enumerate(nearby, 1):
        print(f"   {i}. {obj['name']} ({obj['id']})")

    try:
        choice = int(input("\nEnter object number (0 to cancel): "))
        if choice == 0:
            return
        if 1 <= choice <= len(nearby):
            obj = nearby[choice - 1]
            print_status(f"Attempting to pick up {obj['name']}...", "blue")

            result = make_request("POST", f"/assistant/pick-up/{obj['id']}")
            if result.get("success"):
                print_status(f"✅ Successfully picked up {obj['name']}!", "green")
            else:
                print_status(f"❌ Failed to pick up {obj['name']}: {result.get('data', {}).get('detail', 'Unknown error')}", "red")
        else:
            print_status("Invalid choice", "red")
    except (ValueError, KeyboardInterrupt):
        print_status("Cancelled", "yellow")

def test_put_down():
    """Test putting down the held object"""
    print_status("📦 Put Down Object Test", "yellow")

    holding = get_holding_status()
    if not holding.get("holding_object_id"):
        print_status("Not holding any object. Pick up an object first.", "red")
        return

    print(f"Currently holding: {holding['holding_object_name']}")
    print("\nPut down options:")
    print("1. Put down at current location")
    print("2. Put down at specific location")
    print("0. Cancel")

    try:
        choice = int(input("\nEnter choice: "))

        if choice == 0:
            return
        elif choice == 1:
            # Put down at current location
            result = make_request("POST", "/assistant/put-down")
            if result.get("success"):
                print_status("✅ Successfully put down object at current location!", "green")
            else:
                print_status(f"❌ Failed to put down object: {result.get('data', {}).get('detail', 'Unknown error')}", "red")

        elif choice == 2:
            # Put down at specific location
            x = int(input("Enter X coordinate (0-63): "))
            y = int(input("Enter Y coordinate (0-15): "))

            data = {"position": {"x": x, "y": y}}
            result = make_request("POST", "/assistant/put-down", data)
            if result.get("success"):
                print_status(f"✅ Successfully put down object at ({x}, {y})!", "green")
            else:
                print_status(f"❌ Failed to put down object: {result.get('data', {}).get('detail', 'Unknown error')}", "red")
        else:
            print_status("Invalid choice", "red")

    except (ValueError, KeyboardInterrupt):
        print_status("Cancelled", "yellow")

def test_move_assistant():
    """Test moving the assistant"""
    print_status("🚶 Move Assistant Test", "yellow")

    try:
        x = int(input("Enter X coordinate (0-63): "))
        y = int(input("Enter Y coordinate (0-15): "))

        data = {"x": x, "y": y}
        result = make_request("PUT", "/assistant/position", data)
        if result.get("success"):
            print_status(f"✅ Successfully moved assistant to ({x}, {y})!", "green")
        else:
            print_status(f"❌ Failed to move assistant: {result.get('data', {}).get('detail', 'Unknown error')}", "red")

    except (ValueError, KeyboardInterrupt):
        print_status("Cancelled", "yellow")

def test_brain_council():
    """Test Brain Council object manipulation"""
    print_status("🧠 Brain Council Object Manipulation Test", "yellow")

    print("Enter a message for the Brain Council to process.")
    print("Examples:")
    print("  - 'pick up the mug'")
    print("  - 'put the object on the desk'")
    print("  - 'move the lamp to the corner'")

    try:
        message = input("\nEnter message: ").strip()
        if not message:
            return

        data = {
            "message": message,
            "persona": {"name": "Alice", "personality": "helpful assistant"}
        }

        print_status(f"Processing: '{message}'...", "blue")
        result = make_request("POST", "/brain/process", data)

        if result.get("success"):
            response_data = result["data"]
            print_status("✅ Brain Council Response:", "green")
            print(f"   💬 Response: {response_data.get('response', 'No response')}")

            actions = response_data.get('actions', [])
            if actions:
                print(f"   🎯 Proposed Actions ({len(actions)}):")
                for i, action in enumerate(actions, 1):
                    print(f"      {i}. {action.get('type', 'unknown')} -> {action.get('target', 'unknown')}")
            else:
                print("   🎯 No actions proposed")

            print(f"   😊 Mood: {response_data.get('mood', 'neutral')}")
        else:
            print_status(f"❌ Failed to process message: {result.get('error', 'Unknown error')}", "red")

    except KeyboardInterrupt:
        print_status("Cancelled", "yellow")

def run_full_test_scenario():
    """Run a full test scenario"""
    print_status("🚀 Running Full Object Manipulation Scenario", "purple")
    print()

    # Step 1: Check initial state
    print("Step 1: Checking initial state...")
    show_assistant_status()
    time.sleep(1)

    # Step 2: Move to objects
    print("Step 2: Moving to object area...")
    move_result = make_request("PUT", "/assistant/position", {"x": 15, "y": 8})
    if move_result.get("success"):
        print_status("✅ Moved to object area", "green")
    else:
        print_status("❌ Failed to move", "red")
        return
    time.sleep(1)

    # Step 3: List nearby objects
    print("Step 3: Scanning for nearby objects...")
    nearby = list_nearby_objects()
    time.sleep(1)

    # Step 4: Try to pick up first available object
    if nearby:
        obj = nearby[0]
        print(f"Step 4: Attempting to pick up {obj['name']}...")
        pickup_result = make_request("POST", f"/assistant/pick-up/{obj['id']}")
        if pickup_result.get("success"):
            print_status(f"✅ Picked up {obj['name']}", "green")

            # Step 5: Move while holding object
            print("Step 5: Moving while holding object...")
            move_result = make_request("PUT", "/assistant/position", {"x": 25, "y": 10})
            if move_result.get("success"):
                print_status("✅ Moved while holding object", "green")
            time.sleep(1)

            # Step 6: Put down object
            print("Step 6: Putting down object...")
            putdown_result = make_request("POST", "/assistant/put-down")
            if putdown_result.get("success"):
                print_status("✅ Put down object", "green")
            else:
                print_status("❌ Failed to put down object", "red")
        else:
            print_status(f"❌ Failed to pick up {obj['name']}", "red")
    else:
        print_status("❌ No movable objects found", "red")

    print()
    print_status("🎉 Full scenario test completed!", "purple")

def main_menu():
    """Main interactive menu"""
    while True:
        print_banner()
        show_assistant_status()

        print("🎮 Test Menu:")
        print("1. 🔍 List nearby objects")
        print("2. 📦 Pick up object")
        print("3. 📤 Put down object")
        print("4. 🚶 Move assistant")
        print("5. 🧠 Test Brain Council")
        print("6. 🚀 Run full test scenario")
        print("0. ❌ Exit")
        print()

        try:
            choice = input("Enter your choice: ").strip()
            print()

            if choice == "0":
                print_status("👋 Goodbye!", "cyan")
                break
            elif choice == "1":
                list_nearby_objects()
            elif choice == "2":
                test_pick_up()
            elif choice == "3":
                test_put_down()
            elif choice == "4":
                test_move_assistant()
            elif choice == "5":
                test_brain_council()
            elif choice == "6":
                run_full_test_scenario()
            else:
                print_status("Invalid choice. Please try again.", "red")

            input("\nPress Enter to continue...")
            print("\n" * 2)

        except KeyboardInterrupt:
            print_status("\n👋 Goodbye!", "cyan")
            break
        except Exception as e:
            print_status(f"Error: {e}", "red")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    print_status("Starting Interactive Object Manipulation Test...", "blue")
    print_status("Make sure the backend is running at http://localhost:8000", "yellow")
    print()

    # Test connection
    health_check = make_request("GET", "/health")
    if not health_check.get("success"):
        print_status("❌ Cannot connect to backend API. Please start the backend service.", "red")
        exit(1)

    print_status("✅ Connected to backend API", "green")
    input("Press Enter to start...")

    main_menu()