#!/usr/bin/env python3
"""
Phase 10 Interactive Test Suite - Manual UI/UX Testing Guide
Provides step-by-step testing instructions for all Phase 10 features
"""

import time
import requests
import json
from typing import Dict, Any

# ANSI color codes
class Colors:
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    WHITE = '\033[1;37m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header(text: str):
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.WHITE}{text}{Colors.NC}")
    print(f"{Colors.PURPLE}{'=' * 80}{Colors.NC}")

def print_step(step: str):
    print(f"{Colors.CYAN}🔹 {step}{Colors.NC}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.NC}")

def wait_for_user(prompt: str = "Press Enter to continue..."):
    input(f"{Colors.YELLOW}{prompt}{Colors.NC}")

def get_user_confirmation(question: str) -> bool:
    while True:
        response = input(f"{Colors.CYAN}{question} (y/n): {Colors.NC}").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")

def check_backend_health() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_frontend_health() -> bool:
    """Check if frontend is running"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_settings_panel():
    """Interactive test for settings panel functionality"""
    print_header("🎛️ SETTINGS PANEL TESTING")

    print_step("1. Open the frontend at http://localhost:3000")
    wait_for_user()

    print_step("2. Look for the settings gear icon in the header (both mobile and desktop)")
    if not get_user_confirmation("Can you see the settings gear icon?"):
        print_error("Settings button not visible - check App.tsx integration")
        return False

    print_step("3. Click the settings gear icon")
    wait_for_user()

    print_step("4. Verify the settings modal opens with tabs")
    if not get_user_confirmation("Did the settings modal open with multiple tabs?"):
        print_error("Settings modal not working - check SettingsPanel component")
        return False

    print_step("5. Test each settings tab:")

    tabs = [
        ("Display", "Theme, grid mode, animations, performance toggles"),
        ("AI Models", "Provider selection, model settings, temperature"),
        ("Chat", "Timestamps, typing indicator, font size"),
        ("Notifications", "Various notification toggles"),
        ("Debug", "Debug mode and log level settings")
    ]

    for tab_name, description in tabs:
        print_step(f"   • Click '{tab_name}' tab - should show: {description}")
        if not get_user_confirmation(f"Does the {tab_name} tab work correctly?"):
            print_error(f"{tab_name} tab has issues")
            return False

    print_step("6. Test settings persistence:")
    print_step("   • Change a setting (e.g., toggle FPS counter)")
    print_step("   • Close settings modal")
    print_step("   • Reopen settings modal")
    if not get_user_confirmation("Did your setting change persist?"):
        print_error("Settings persistence not working")
        return False

    print_step("7. Test reset functionality")
    print_step("   • Click 'Reset' button for any category")
    if not get_user_confirmation("Did the reset button work?"):
        print_error("Reset functionality has issues")
        return False

    print_success("Settings panel test completed!")
    return True

def test_time_display():
    """Interactive test for time display component"""
    print_header("🕐 TIME DISPLAY TESTING")

    print_step("1. Look for the time display in the chat panel")
    if not get_user_confirmation("Can you see a time display showing current time and date?"):
        print_error("Time display not visible - check TimeDisplay integration")
        return False

    print_step("2. Verify real-time updates")
    print_step("   • Watch the time display for 10 seconds")
    wait_for_user("Wait 10 seconds and observe...")
    if not get_user_confirmation("Did you see the time update in real-time?"):
        print_error("Time not updating - check useEffect timer")
        return False

    print_step("3. Check formatting elements:")
    elements = [
        "Current time (hours:minutes:seconds)",
        "Current date with weekday",
        "Time-of-day greeting (Morning/Afternoon/Evening/Night)"
    ]

    for element in elements:
        if not get_user_confirmation(f"Can you see: {element}?"):
            print_error(f"Missing element: {element}")
            return False

    print_success("Time display test completed!")
    return True

def test_status_indicators():
    """Interactive test for enhanced status indicators"""
    print_header("📊 STATUS INDICATORS TESTING")

    print_step("1. Look for status indicators in the companion area")
    if not get_user_confirmation("Can you see colorful status indicators next to the persona?"):
        print_error("Status indicators not visible - check StatusIndicators integration")
        return False

    print_step("2. Verify mood indicator")
    print_step("   • Should show emoji and color based on assistant mood")
    if not get_user_confirmation("Is there a mood indicator with emoji and color?"):
        print_error("Mood indicator not working")
        return False

    print_step("3. Verify status indicator")
    print_step("   • Should show active/idle/busy status with appropriate icon")
    if not get_user_confirmation("Is there a status indicator showing assistant mode?"):
        print_error("Status indicator not working")
        return False

    print_step("4. Check for action indicator")
    if get_user_confirmation("Is the assistant currently performing an action?"):
        if not get_user_confirmation("Do you see an action indicator icon?"):
            print_error("Action indicator not working")
            return False

    print_step("5. Test mood changes (if possible)")
    print_step("   • Try triggering a mood change via chat or brain council")
    print_step("   • Observe if indicators update")
    wait_for_user("Try to change assistant mood and observe...")

    print_success("Status indicators test completed!")
    return True

def test_expression_transitions():
    """Interactive test for expression transition system"""
    print_header("🎭 EXPRESSION TRANSITIONS TESTING")

    print_step("1. Look at the assistant portrait")
    if not get_user_confirmation("Can you see the enhanced portrait with status dots?"):
        print_error("Enhanced portrait not visible - check ExpressionDisplay integration")
        return False

    print_step("2. Check for status indicator dots")
    print_step("   • Top-right corner should have small colored dots")
    if not get_user_confirmation("Are there status dots in the corner of the portrait?"):
        print_error("Status dots not visible")
        return False

    print_step("3. Test expression transitions (if available)")
    print_step("   • Try changing expressions via persona selector or brain council")
    print_step("   • Look for smooth fade transitions")
    wait_for_user("Try to trigger expression changes...")

    if get_user_confirmation("Did you observe any expression transitions?"):
        if not get_user_confirmation("Were the transitions smooth with fade effects?"):
            print_error("Transition animations not working properly")
            return False

    print_step("4. Test mood overlay")
    print_step("   • Try triggering mood changes")
    print_step("   • Look for brief colored overlay flash")
    wait_for_user("Try to trigger mood changes...")

    print_success("Expression transitions test completed!")
    return True

def test_performance_monitoring():
    """Interactive test for performance monitoring"""
    print_header("📈 PERFORMANCE MONITORING TESTING")

    print_step("1. Open settings and go to Display tab")
    wait_for_user()

    print_step("2. Enable 'Show FPS Counter'")
    wait_for_user()

    print_step("3. Look for FPS counter in top-left corner")
    if not get_user_confirmation("Can you see an FPS counter in the top-left?"):
        print_error("FPS counter not working - check PerformanceMonitor component")
        return False

    print_step("4. Enable 'Show Performance Metrics'")
    wait_for_user()

    print_step("5. Look for detailed performance panel in top-right")
    if not get_user_confirmation("Can you see a detailed performance panel in top-right?"):
        print_error("Performance metrics not working")
        return False

    print_step("6. Verify performance metrics content:")
    metrics = [
        "FPS with status (Excellent/Good/Fair/Poor)",
        "Frame time in milliseconds",
        "Mini-graphs showing performance trends",
        "Memory usage (if supported by browser)",
        "System information (browser, platform, CPU cores)"
    ]

    for metric in metrics:
        if not get_user_confirmation(f"Can you see: {metric}?"):
            print_warning(f"Metric not visible: {metric}")

    print_step("7. Test performance impact")
    print_step("   • Try scrolling, opening modals, triggering animations")
    print_step("   • Observe if FPS and performance metrics update")
    wait_for_user("Test various interactions and observe metrics...")

    print_success("Performance monitoring test completed!")
    return True

def test_overall_polish():
    """Test overall UI polish and responsiveness"""
    print_header("✨ OVERALL UI POLISH TESTING")

    print_step("1. Test responsive design")
    print_step("   • Resize browser window to test mobile/desktop layouts")
    if not get_user_confirmation("Does the layout adapt properly to different sizes?"):
        print_error("Responsive design issues")
        return False

    print_step("2. Test animation smoothness")
    print_step("   • Open/close modals, change settings, trigger transitions")
    if not get_user_confirmation("Are all animations smooth and polished?"):
        print_warning("Some animations may need optimization")

    print_step("3. Test accessibility")
    print_step("   • Try keyboard navigation (Tab, Enter, Escape)")
    print_step("   • Check tooltips on hover")
    if not get_user_confirmation("Is keyboard navigation working well?"):
        print_warning("Accessibility could be improved")

    print_step("4. Test error handling")
    print_step("   • Try edge cases (invalid inputs, network issues)")
    wait_for_user("Test error scenarios...")

    print_success("Overall polish test completed!")
    return True

def main():
    """Run the complete Phase 10 interactive test suite"""
    print_header("🎨 PHASE 10 UI/UX POLISH - INTERACTIVE TEST SUITE")

    print_info("This interactive test suite will guide you through testing all Phase 10 features:")
    print_info("• Settings Panel Infrastructure")
    print_info("• Time/Date Display")
    print_info("• Enhanced Status Indicators")
    print_info("• Expression Transitions")
    print_info("• Performance Monitoring")
    print_info("• Overall UI Polish")
    print()

    # Check prerequisites
    print_header("🔍 Prerequisites Check")

    if not check_backend_health():
        print_error("Backend not running! Start with: docker-compose up -d")
        return
    print_success("Backend is running")

    if not check_frontend_health():
        print_error("Frontend not running! Start with: npm run dev")
        return
    print_success("Frontend is running")

    print()
    wait_for_user("Ready to begin interactive testing? Press Enter...")

    # Run test sections
    test_results = []

    tests = [
        ("Settings Panel", test_settings_panel),
        ("Time Display", test_time_display),
        ("Status Indicators", test_status_indicators),
        ("Expression Transitions", test_expression_transitions),
        ("Performance Monitoring", test_performance_monitoring),
        ("Overall Polish", test_overall_polish)
    ]

    for test_name, test_func in tests:
        print()
        if get_user_confirmation(f"Test {test_name}?"):
            result = test_func()
            test_results.append((test_name, result))
        else:
            print_warning(f"Skipped {test_name}")
            test_results.append((test_name, None))

    # Final summary
    print_header("📊 TEST RESULTS SUMMARY")

    passed_count = sum(1 for _, result in test_results if result is True)
    failed_count = sum(1 for _, result in test_results if result is False)
    skipped_count = sum(1 for _, result in test_results if result is None)

    print()
    for test_name, result in test_results:
        if result is True:
            print_success(f"{test_name}: PASSED")
        elif result is False:
            print_error(f"{test_name}: FAILED")
        else:
            print_warning(f"{test_name}: SKIPPED")

    print()
    print(f"{Colors.WHITE}Phase 10 Interactive Test Results:{Colors.NC}")
    print(f"{Colors.GREEN}✅ Passed: {passed_count}{Colors.NC}")
    print(f"{Colors.RED}❌ Failed: {failed_count}{Colors.NC}")
    print(f"{Colors.YELLOW}⏭️  Skipped: {skipped_count}{Colors.NC}")

    if failed_count == 0:
        print()
        print_success("🎉 All tested Phase 10 features are working correctly!")
        print_info("🚀 Phase 10 UI/UX Polish implementation is complete!")
    else:
        print()
        print_warning(f"⚠️  {failed_count} test(s) failed - review implementation")

    print()
    print_info("Frontend URL: http://localhost:3000")
    print_info("Backend API: http://localhost:8000/docs")

if __name__ == "__main__":
    main()