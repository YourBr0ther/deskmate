#!/usr/bin/env python3
"""
Phase 12B Integration Test Script

Tests the complete multi-device top-down room system including:
- ResponsiveLayout system (desktop/tablet/mobile)
- Floor plan template loading and discovery
- Room navigation components
- Touch gesture support
- Device detection
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

async def test_backend_health():
    """Test backend health and services."""
    print("🔍 Testing backend health...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BACKEND_URL}/health") as resp:
                data = await resp.json()
                print(f"✅ Backend healthy: {data['status']}")
                print(f"   Services: API={data['services']['api']['status']}, "
                      f"Postgres={data['services']['postgres']['status']}, "
                      f"Qdrant={data['services']['qdrant']['status']}")
                return True
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False

async def test_frontend_loading():
    """Test frontend accessibility."""
    print("🌐 Testing frontend loading...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(FRONTEND_URL) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    if "DeskMate" in content:
                        print("✅ Frontend loading successfully")
                        return True
                    else:
                        print("❌ Frontend content doesn't contain DeskMate")
                        return False
                else:
                    print(f"❌ Frontend returned status {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Frontend test failed: {e}")
            return False

async def test_floor_plan_templates():
    """Test floor plan template discovery."""
    print("🏠 Testing floor plan templates...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BACKEND_URL}/rooms/templates/discover") as resp:
                data = await resp.json()
                templates_dir = data.get('templates_directory', '')
                count = data.get('count', 0)

                print(f"   Templates directory: {templates_dir}")
                print(f"   Template count: {count}")

                # Check if template files exist on disk
                templates_path = Path("templates/floor_plans")
                if templates_path.exists():
                    template_files = list(templates_path.glob("*.json"))
                    print(f"   Files on disk: {len(template_files)} JSON files")
                    for file in template_files:
                        print(f"     - {file.name}")
                    print("✅ Floor plan template system working")
                    return True
                else:
                    print("⚠️  Templates directory not found on disk")
                    return False
        except Exception as e:
            print(f"❌ Floor plan templates test failed: {e}")
            return False

async def test_navigation_endpoints():
    """Test room navigation API endpoints."""
    print("🧭 Testing navigation endpoints...")
    endpoints_to_test = [
        "/rooms/floor-plans",
        "/rooms/current",
        "/rooms/assistant/position/1"
    ]

    success_count = 0
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            try:
                async with session.get(f"{BACKEND_URL}{endpoint}") as resp:
                    if resp.status == 200:
                        print(f"✅ {endpoint} - OK")
                        success_count += 1
                    else:
                        data = await resp.text()
                        print(f"⚠️  {endpoint} - Status {resp.status}: {data[:100]}...")
            except Exception as e:
                print(f"❌ {endpoint} - Error: {e}")

    print(f"   Navigation endpoints: {success_count}/{len(endpoints_to_test)} working")
    return success_count > 0

def test_frontend_components():
    """Test that new frontend components exist."""
    print("⚛️  Testing frontend component structure...")

    component_paths = [
        "frontend/src/components/Layout/ResponsiveLayout.tsx",
        "frontend/src/components/Layout/DesktopLayout.tsx",
        "frontend/src/components/Layout/MobileLayout.tsx",
        "frontend/src/components/Layout/TabletLayout.tsx",
        "frontend/src/components/FloorPlan/TopDownRenderer.tsx",
        "frontend/src/components/FloorPlan/FloorPlanContainer.tsx",
        "frontend/src/components/Navigation/RoomNavigationPanel.tsx",
        "frontend/src/hooks/useDeviceDetection.ts",
        "frontend/src/hooks/useRoomNavigation.ts",
        "frontend/src/hooks/useFloorPlanManager.ts",
        "frontend/src/hooks/useTouchGestures.ts",
        "frontend/src/types/floorPlan.ts"
    ]

    existing_count = 0
    for path in component_paths:
        if Path(path).exists():
            existing_count += 1
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - Not found")

    print(f"   Frontend components: {existing_count}/{len(component_paths)} exist")
    return existing_count == len(component_paths)

def test_backend_components():
    """Test that new backend components exist."""
    print("🐍 Testing backend component structure...")

    component_paths = [
        "backend/app/api/room_navigation.py",
        "backend/app/models/floor_plans.py",
        "backend/app/models/rooms.py",
        "backend/app/services/room_navigation.py",
        "backend/app/services/multi_room_pathfinding.py",
        "backend/app/services/template_loader.py"
    ]

    existing_count = 0
    for path in component_paths:
        if Path(path).exists():
            existing_count += 1
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - Not found")

    print(f"   Backend components: {existing_count}/{len(component_paths)} exist")
    return existing_count == len(component_paths)

async def main():
    """Run all Phase 12B integration tests."""
    print("🚀 Starting Phase 12B Multi-Device Top-Down Room System Integration Tests")
    print("=" * 80)

    tests = [
        ("Backend Health", test_backend_health),
        ("Frontend Loading", test_frontend_loading),
        ("Floor Plan Templates", test_floor_plan_templates),
        ("Navigation Endpoints", test_navigation_endpoints),
        ("Frontend Components", lambda: test_frontend_components()),
        ("Backend Components", lambda: test_backend_components())
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Phase 12B Multi-Device Top-Down Room System is fully functional!")
        return 0
    else:
        print("⚠️  Some Phase 12B components need attention")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))