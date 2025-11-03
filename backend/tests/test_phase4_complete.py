#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 4: Assistant Movement & Pathfinding

This test verifies all Phase 4 requirements according to DESKMATE_SPEC.md:

Phase 4 Deliverables:
- A* pathfinding algorithm
- Assistant sprite/representation on grid
- Walking animation (grid-hop)
- Collision detection (can't walk through large objects)
- Walk-through for small objects
- Sitting on furniture
- Position tracking in database

Acceptance Criteria:
- Assistant can pathfind to any reachable cell
- Walks around furniture
- Can sit on bed/chair
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any, List, Tuple, Set

# Test configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class Phase4TestSuite:
    """Comprehensive Phase 4 test suite."""

    def __init__(self):
        self.base_url = BASE_URL
        self.frontend_url = FRONTEND_URL
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")

    def test_system_health(self) -> bool:
        """Test that all required services are running."""
        print("\n🔍 Testing System Health...")

        try:
            # Test backend health
            response = requests.get(f"{self.base_url}/health", timeout=5)
            backend_healthy = response.status_code == 200

            # Test frontend accessibility
            response = requests.get(f"{self.frontend_url}", timeout=5)
            frontend_healthy = response.status_code == 200

            # Test database tables exist (via assistant state)
            response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
            database_healthy = response.status_code == 200

            all_healthy = backend_healthy and frontend_healthy and database_healthy

            self.log_test(
                "System Health Check",
                all_healthy,
                f"Backend: {backend_healthy}, Frontend: {frontend_healthy}, Database: {database_healthy}"
            )

            return all_healthy

        except Exception as e:
            self.log_test("System Health Check", False, f"Error: {e}")
            return False

    def test_pathfinding_algorithm(self) -> bool:
        """Test A* pathfinding algorithm implementation."""
        print("\n🔍 Testing A* Pathfinding Algorithm...")

        tests_passed = 0
        total_tests = 4

        try:
            # Test 1: Basic pathfinding to empty space
            response = requests.post(
                f"{self.base_url}/assistant/pathfind",
                json={"target": {"x": 40, "y": 10}},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("path_found") and len(result.get("path", [])) > 0:
                    tests_passed += 1
                    self.log_test("Pathfinding to Empty Space", True, f"Path length: {result.get('path_length')}")
                else:
                    self.log_test("Pathfinding to Empty Space", False, "No path found to valid position")

            # Test 2: Pathfinding blocked by obstacles
            response = requests.post(
                f"{self.base_url}/assistant/pathfind",
                json={"target": {"x": 52, "y": 14}},  # Inside bed
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if not result.get("path_found"):
                    tests_passed += 1
                    self.log_test("Pathfinding Blocked by Obstacles", True, "Correctly blocked by bed")
                else:
                    self.log_test("Pathfinding Blocked by Obstacles", False, "Found path to blocked position")

            # Test 3: Pathfinding around obstacles
            response = requests.post(
                f"{self.base_url}/assistant/pathfind",
                json={"target": {"x": 20, "y": 5}},  # Around desk
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("path_found") and result.get("path_length", 0) > 5:
                    tests_passed += 1
                    self.log_test("Pathfinding Around Obstacles", True, f"Path around obstacles: {result.get('path_length')} steps")
                else:
                    self.log_test("Pathfinding Around Obstacles", False, "Failed to find path around obstacles")

            # Test 4: Edge case - out of bounds
            response = requests.post(
                f"{self.base_url}/assistant/pathfind",
                json={"target": {"x": 100, "y": 100}},  # Out of bounds
                timeout=10
            )

            if response.status_code == 400:  # Should reject invalid coordinates
                tests_passed += 1
                self.log_test("Pathfinding Edge Cases", True, "Correctly rejected out-of-bounds coordinates")
            else:
                self.log_test("Pathfinding Edge Cases", False, "Did not reject invalid coordinates")

        except Exception as e:
            self.log_test("Pathfinding Algorithm Tests", False, f"Error: {e}")
            return False

        success = tests_passed == total_tests
        self.log_test(f"A* Pathfinding Algorithm Complete", success, f"{tests_passed}/{total_tests} tests passed")
        return success

    def test_assistant_movement(self) -> bool:
        """Test assistant movement with collision detection."""
        print("\n🔍 Testing Assistant Movement...")

        tests_passed = 0
        total_tests = 3

        try:
            # Get initial position
            response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
            if response.status_code != 200:
                self.log_test("Assistant Movement", False, "Cannot get initial assistant state")
                return False

            initial_state = response.json()
            initial_pos = initial_state["position"]

            # Test 1: Successful movement to valid position
            target_pos = {"x": 25, "y": 8}
            response = requests.post(
                f"{self.base_url}/assistant/move",
                json={"target": target_pos},
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Verify position was updated
                    response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
                    if response.status_code == 200:
                        current_state = response.json()
                        current_pos = current_state["position"]
                        if current_pos["x"] == target_pos["x"] and current_pos["y"] == target_pos["y"]:
                            tests_passed += 1
                            self.log_test("Movement to Valid Position", True, f"Moved from {initial_pos} to {current_pos}")
                        else:
                            self.log_test("Movement to Valid Position", False, f"Position not updated correctly")
                else:
                    self.log_test("Movement to Valid Position", False, f"Movement failed: {result.get('error')}")

            # Test 2: Movement blocked by obstacles
            response = requests.post(
                f"{self.base_url}/assistant/move",
                json={"target": {"x": 52, "y": 14}},  # Inside bed
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if not result.get("success"):
                    tests_passed += 1
                    self.log_test("Movement Blocked by Obstacles", True, "Correctly blocked movement to bed")
                else:
                    self.log_test("Movement Blocked by Obstacles", False, "Movement to blocked position succeeded")

            # Test 3: Movement around obstacles (long path)
            response = requests.post(
                f"{self.base_url}/assistant/move",
                json={"target": {"x": 55, "y": 8}},  # Far right, around bed
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("path_length", 0) > 10:
                    tests_passed += 1
                    self.log_test("Movement Around Obstacles", True, f"Successfully navigated {result.get('path_length')}-step path")
                else:
                    self.log_test("Movement Around Obstacles", False, "Failed to navigate around obstacles")

        except Exception as e:
            self.log_test("Assistant Movement Tests", False, f"Error: {e}")
            return False

        success = tests_passed == total_tests
        self.log_test(f"Assistant Movement Complete", success, f"{tests_passed}/{total_tests} tests passed")
        return success

    def test_collision_detection(self) -> bool:
        """Test collision detection for movement."""
        print("\n🔍 Testing Collision Detection...")

        tests_passed = 0
        total_tests = 4

        try:
            # Test collision with each furniture piece
            furniture_positions = [
                {"name": "bed", "pos": {"x": 52, "y": 14}},
                {"name": "desk", "pos": {"x": 12, "y": 3}},
                {"name": "window", "pos": {"x": 32, "y": 0}},  # Should be walkable (not solid)
                {"name": "door", "pos": {"x": 0, "y": 9}}       # Should be walkable (not solid)
            ]

            for furniture in furniture_positions:
                response = requests.post(
                    f"{self.base_url}/assistant/move",
                    json={"target": furniture["pos"]},
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()

                    # Bed and desk should block movement (solid=true)
                    if furniture["name"] in ["bed", "desk"]:
                        if not result.get("success"):
                            tests_passed += 1
                            self.log_test(f"Collision Detection - {furniture['name']}", True, "Correctly blocked by solid furniture")
                        else:
                            self.log_test(f"Collision Detection - {furniture['name']}", False, "Movement to solid furniture succeeded")

                    # Window and door should allow movement (solid=false)
                    else:
                        if result.get("success"):
                            tests_passed += 1
                            self.log_test(f"Walk-through - {furniture['name']}", True, "Correctly walked through non-solid object")
                        else:
                            self.log_test(f"Walk-through - {furniture['name']}", False, "Failed to walk through non-solid object")

        except Exception as e:
            self.log_test("Collision Detection Tests", False, f"Error: {e}")
            return False

        success = tests_passed == total_tests
        self.log_test(f"Collision Detection Complete", success, f"{tests_passed}/{total_tests} tests passed")
        return success

    def test_furniture_interaction(self) -> bool:
        """Test sitting on furniture."""
        print("\n🔍 Testing Furniture Interaction...")

        tests_passed = 0
        total_tests = 2

        try:
            # Test sitting on bed
            response = requests.post(
                f"{self.base_url}/assistant/sit",
                json={"furniture_id": "bed"},
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("action") == "sitting":
                    # Verify assistant state shows sitting
                    response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
                    if response.status_code == 200:
                        state = response.json()
                        if (state["status"]["action"] == "sitting" and
                            state["interaction"]["sitting_on"] == "bed"):
                            tests_passed += 1
                            self.log_test("Sitting on Bed", True, f"Position: {state['position']}")
                        else:
                            self.log_test("Sitting on Bed", False, "Assistant state not updated correctly")
                else:
                    self.log_test("Sitting on Bed", False, f"Sitting failed: {result.get('error')}")

            # Test sitting on desk
            response = requests.post(
                f"{self.base_url}/assistant/sit",
                json={"furniture_id": "desk"},
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("action") == "sitting":
                    # Verify assistant state shows sitting on desk
                    response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
                    if response.status_code == 200:
                        state = response.json()
                        if (state["status"]["action"] == "sitting" and
                            state["interaction"]["sitting_on"] == "desk"):
                            tests_passed += 1
                            self.log_test("Sitting on Desk", True, f"Position: {state['position']}")
                        else:
                            self.log_test("Sitting on Desk", False, "Assistant state not updated correctly")
                else:
                    self.log_test("Sitting on Desk", False, f"Sitting failed: {result.get('error')}")

        except Exception as e:
            self.log_test("Furniture Interaction Tests", False, f"Error: {e}")
            return False

        success = tests_passed == total_tests
        self.log_test(f"Furniture Interaction Complete", success, f"{tests_passed}/{total_tests} tests passed")
        return success

    def test_position_tracking(self) -> bool:
        """Test database position tracking and state persistence."""
        print("\n🔍 Testing Position Tracking...")

        tests_passed = 0
        total_tests = 3

        try:
            # Test 1: State persistence
            response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
            if response.status_code == 200:
                state = response.json()
                required_fields = ["position", "facing", "movement", "status", "timestamps"]
                if all(field in state for field in required_fields):
                    tests_passed += 1
                    self.log_test("State Structure", True, "All required state fields present")
                else:
                    missing = [f for f in required_fields if f not in state]
                    self.log_test("State Structure", False, f"Missing fields: {missing}")

            # Test 2: Action logging
            response = requests.get(f"{self.base_url}/assistant/actions/log?limit=5", timeout=5)
            if response.status_code == 200:
                log = response.json()
                if "actions" in log and len(log["actions"]) > 0:
                    action = log["actions"][0]
                    if "action" in action and "created_at" in action:
                        tests_passed += 1
                        self.log_test("Action Logging", True, f"Found {len(log['actions'])} logged actions")
                    else:
                        self.log_test("Action Logging", False, "Invalid action log structure")
                else:
                    self.log_test("Action Logging", False, "No actions found in log")

            # Test 3: Timestamps update
            old_response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
            old_timestamp = old_response.json()["timestamps"]["updated_at"]

            # Trigger position update
            requests.put(
                f"{self.base_url}/assistant/position",
                json={"x": 30, "y": 8},
                timeout=10
            )

            new_response = requests.get(f"{self.base_url}/assistant/state", timeout=5)
            new_timestamp = new_response.json()["timestamps"]["updated_at"]

            if new_timestamp != old_timestamp:
                tests_passed += 1
                self.log_test("Timestamp Updates", True, "Timestamps update correctly")
            else:
                self.log_test("Timestamp Updates", False, "Timestamps not updating")

        except Exception as e:
            self.log_test("Position Tracking Tests", False, f"Error: {e}")
            return False

        success = tests_passed == total_tests
        self.log_test(f"Position Tracking Complete", success, f"{tests_passed}/{total_tests} tests passed")
        return success

    def test_reachability_analysis(self) -> bool:
        """Test that assistant can reach most of the room."""
        print("\n🔍 Testing Reachability Analysis...")

        try:
            response = requests.get(f"{self.base_url}/assistant/reachable", timeout=10)

            if response.status_code == 200:
                result = response.json()
                reachable_count = result.get("count", 0)
                total_cells = 64 * 16  # 1024 total grid cells

                # Should be able to reach at least 90% of the room
                coverage_ratio = reachable_count / total_cells

                if coverage_ratio >= 0.90:
                    self.log_test(
                        "Reachability Coverage",
                        True,
                        f"{reachable_count}/{total_cells} cells reachable ({coverage_ratio:.1%})"
                    )
                    return True
                else:
                    self.log_test(
                        "Reachability Coverage",
                        False,
                        f"Only {coverage_ratio:.1%} coverage, expected >90%"
                    )
                    return False
            else:
                self.log_test("Reachability Analysis", False, f"API error: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Reachability Analysis", False, f"Error: {e}")
            return False

    def test_frontend_integration(self) -> bool:
        """Test frontend integration with assistant system."""
        print("\n🔍 Testing Frontend Integration...")

        tests_passed = 0
        total_tests = 2

        try:
            # Test 1: Frontend can access assistant API through proxy
            response = requests.get(f"{self.frontend_url}/api/assistant/state", timeout=5)
            if response.status_code == 200:
                tests_passed += 1
                self.log_test("Frontend API Proxy", True, "Assistant API accessible through frontend")
            else:
                self.log_test("Frontend API Proxy", False, f"API proxy failed: {response.status_code}")

            # Test 2: Frontend can access movement API
            response = requests.post(
                f"{self.frontend_url}/api/assistant/move",
                json={"target": {"x": 35, "y": 8}},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    tests_passed += 1
                    self.log_test("Frontend Movement Integration", True, "Movement API works through frontend")
                else:
                    self.log_test("Frontend Movement Integration", False, f"Movement failed: {result.get('error')}")
            else:
                self.log_test("Frontend Movement Integration", False, f"API call failed: {response.status_code}")

        except Exception as e:
            self.log_test("Frontend Integration Tests", False, f"Error: {e}")
            return False

        success = tests_passed == total_tests
        self.log_test(f"Frontend Integration Complete", success, f"{tests_passed}/{total_tests} tests passed")
        return success

    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete Phase 4 test suite."""
        print("🚀 Running Complete Phase 4 Test Suite")
        print("=" * 60)

        test_methods = [
            self.test_system_health,
            self.test_pathfinding_algorithm,
            self.test_assistant_movement,
            self.test_collision_detection,
            self.test_furniture_interaction,
            self.test_position_tracking,
            self.test_reachability_analysis,
            self.test_frontend_integration
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_method.__name__} crashed: {e}")

        # Generate summary
        success_rate = passed_tests / total_tests
        overall_success = success_rate >= 1.0

        print("\n" + "=" * 60)
        print("📊 PHASE 4 TEST SUMMARY")
        print("=" * 60)

        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    {result['details']}")

        print("\n" + "=" * 60)
        print(f"📈 OVERALL RESULTS: {passed_tests}/{total_tests} major test categories passed")
        print(f"🎯 SUCCESS RATE: {success_rate:.1%}")

        if overall_success:
            print("🎉 PHASE 4 COMPLETE: All tests passed!")
            print("✅ Ready to proceed to Phase 5")
        else:
            print("⚠️  PHASE 4 INCOMPLETE: Some tests failed")
            print("❌ Fix issues before proceeding to Phase 5")

        return {
            "overall_success": overall_success,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "detailed_results": self.test_results
        }


def main():
    """Run the Phase 4 test suite."""
    suite = Phase4TestSuite()

    print("DeskMate Phase 4 Verification Test Suite")
    print("Testing: Assistant Movement & Pathfinding")
    print()

    # Run all tests
    results = suite.run_all_tests()

    # Exit with appropriate code
    exit_code = 0 if results["overall_success"] else 1
    exit(exit_code)


if __name__ == "__main__":
    main()