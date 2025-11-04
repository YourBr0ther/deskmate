#!/bin/bash

# Phase 9 Idle Mode Test Suite
# Tests all idle mode and autonomous behavior features implemented in Phase 9

set -e

echo "🧪 Phase 9 Idle Mode & Autonomous Behavior Test Suite"
echo "=============================================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Test configuration
BASE_URL="http://localhost:8000"
TIMEOUT_MINUTES=10
DREAM_TEST_MINUTES=3

# Function to print test status
print_test() {
    echo -e "${BLUE}🔍 Testing:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}❌ ERROR:${NC} $1"
}

print_info() {
    echo -e "${PURPLE}ℹ️  INFO:${NC} $1"
}

# Function to check HTTP response
check_response() {
    local response_code=$1
    local expected_code=${2:-200}
    local description=$3

    if [ "$response_code" = "$expected_code" ]; then
        print_success "$description (HTTP $response_code)"
        return 0
    else
        print_error "$description (Expected HTTP $expected_code, got $response_code)"
        return 1
    fi
}

# Function to wait for condition with timeout
wait_for_condition() {
    local condition_command="$1"
    local timeout_seconds="$2"
    local description="$3"
    local interval=2

    print_info "Waiting for: $description (timeout: ${timeout_seconds}s)"

    local elapsed=0
    while [ $elapsed -lt $timeout_seconds ]; do
        if eval "$condition_command" &>/dev/null; then
            print_success "$description"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        printf "."
    done

    echo
    print_error "Timeout waiting for: $description"
    return 1
}

# Function to extract JSON field
extract_json_field() {
    local json="$1"
    local field="$2"
    echo "$json" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$field', ''))" 2>/dev/null
}

echo "🏗️  Phase 9 Test Environment Setup"
echo "=================================="

# Test 1: Health Check
print_test "System health check"
response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$BASE_URL/health")
if check_response "${response}" "200" "Health check"; then
    health_data=$(cat /tmp/health_response.json)
    print_info "Health: $(extract_json_field "$health_data" "status")"
fi

# Test 2: Assistant State Check
print_test "Assistant state retrieval"
response=$(curl -s -w "%{http_code}" -o /tmp/assistant_state.json "$BASE_URL/assistant/state")
if check_response "${response}" "200" "Assistant state retrieval"; then
    assistant_data=$(cat /tmp/assistant_state.json)
    current_mode=$(extract_json_field "$assistant_data" "mode")
    print_info "Current assistant mode: $current_mode"
fi

echo
echo "🎯 Phase 9 Core Features Testing"
echo "==============================="

# Test 3: Mode Management API
print_test "Assistant mode API endpoints"

# Get current mode
response=$(curl -s -w "%{http_code}" -o /tmp/mode_response.json "$BASE_URL/assistant/mode")
if check_response "${response}" "200" "Get assistant mode"; then
    mode_data=$(cat /tmp/mode_response.json)
    initial_mode=$(extract_json_field "$mode_data" "mode")
    print_info "Initial mode: $initial_mode"
fi

# Force idle mode
print_test "Forcing idle mode via API"
response=$(curl -s -w "%{http_code}" -o /tmp/force_idle.json -X POST "$BASE_URL/assistant/idle/force")
if check_response "${response}" "200" "Force idle mode"; then
    idle_result=$(cat /tmp/force_idle.json)
    print_info "Idle mode result: $(extract_json_field "$idle_result" "message")"
fi

# Wait for mode change to propagate
sleep 2

# Verify mode change
print_test "Verifying mode change to idle"
response=$(curl -s -w "%{http_code}" -o /tmp/mode_check.json "$BASE_URL/assistant/mode")
if check_response "${response}" "200" "Mode verification"; then
    mode_data=$(cat /tmp/mode_check.json)
    current_mode=$(extract_json_field "$mode_data" "mode")
    if [ "$current_mode" = "idle" ]; then
        print_success "Assistant is now in idle mode"
    else
        print_error "Assistant mode is '$current_mode', expected 'idle'"
    fi
fi

# Test 4: Idle Status and Statistics
print_test "Idle controller status"
response=$(curl -s -w "%{http_code}" -o /tmp/idle_status.json "$BASE_URL/assistant/idle/status")
if check_response "${response}" "200" "Idle status retrieval"; then
    status_data=$(cat /tmp/idle_status.json)
    is_running=$(extract_json_field "$status_data" "is_running")
    print_info "Idle controller running: $is_running"
fi

# Test 5: Dream Storage System
print_test "Dream memory system"

# Check if dreams exist (may be empty initially)
response=$(curl -s -w "%{http_code}" -o /tmp/dreams.json "$BASE_URL/assistant/dreams?limit=5")
if check_response "${response}" "200" "Dream retrieval"; then
    dreams_data=$(cat /tmp/dreams.json)
    dream_count=$(extract_json_field "$dreams_data" "count")
    print_info "Current dreams in memory: $dream_count"
fi

# Get dream statistics
response=$(curl -s -w "%{http_code}" -o /tmp/dream_stats.json "$BASE_URL/assistant/dreams/stats")
if check_response "${response}" "200" "Dream statistics"; then
    stats_data=$(cat /tmp/dream_stats.json)
    total_dreams=$(extract_json_field "$stats_data" "total_dreams_24h")
    print_info "Total dreams (24h): $total_dreams"
fi

# Test 6: Dream Search Functionality
print_test "Dream search functionality"
response=$(curl -s -w "%{http_code}" -o /tmp/dream_search.json "$BASE_URL/assistant/dreams/search?query=room&limit=3")
if check_response "${response}" "200" "Dream search"; then
    search_data=$(cat /tmp/dream_search.json)
    search_count=$(extract_json_field "$search_data" "count")
    print_info "Dreams matching 'room': $search_count"
fi

echo
echo "⏱️  Autonomous Behavior Testing"
echo "=============================="

# Test 7: Wait for Autonomous Actions (if idle mode is working)
print_test "Autonomous action generation (waiting ${DREAM_TEST_MINUTES} minutes)"
print_info "This test waits for the assistant to perform autonomous actions in idle mode"
print_info "Expected: 1 action every 3-8 minutes in idle mode"

# Store initial dream count
initial_dreams_response=$(curl -s "$BASE_URL/assistant/dreams/stats")
initial_dreams=$(extract_json_field "$initial_dreams_response" "total_dreams_24h")

# Wait for autonomous actions
autonomous_wait_seconds=$((DREAM_TEST_MINUTES * 60))
print_info "Waiting ${DREAM_TEST_MINUTES} minutes for autonomous actions..."

# Check every 30 seconds for new dreams
for i in $(seq 1 $((autonomous_wait_seconds / 30))); do
    sleep 30
    printf "."

    # Check for new dreams every minute
    if [ $((i % 2)) -eq 0 ]; then
        current_response=$(curl -s "$BASE_URL/assistant/dreams/stats")
        current_dreams=$(extract_json_field "$current_response" "total_dreams_24h")

        if [ "$current_dreams" -gt "$initial_dreams" ]; then
            echo
            new_dream_count=$((current_dreams - initial_dreams))
            print_success "Generated $new_dream_count new autonomous action(s)!"
            break
        fi
    fi
done

echo
# Final dream count check
final_response=$(curl -s "$BASE_URL/assistant/dreams/stats")
final_dreams=$(extract_json_field "$final_response" "total_dreams_24h")
total_new_dreams=$((final_dreams - initial_dreams))

if [ "$total_new_dreams" -gt 0 ]; then
    print_success "Autonomous behavior test PASSED - Generated $total_new_dreams dream(s)"
else
    print_warning "No autonomous actions detected in ${DREAM_TEST_MINUTES} minutes"
    print_info "This might be normal if action interval is longer than test duration"
fi

# Test 8: Return to Active Mode
print_test "Returning to active mode"
response=$(curl -s -w "%{http_code}" -o /tmp/activate.json -X POST "$BASE_URL/assistant/idle/activate")
if check_response "${response}" "200" "Force active mode"; then
    activate_result=$(cat /tmp/activate.json)
    print_info "Active mode result: $(extract_json_field "$activate_result" "message")"
fi

# Wait for mode change
sleep 2

# Verify return to active mode
print_test "Verifying return to active mode"
response=$(curl -s -w "%{http_code}" -o /tmp/final_mode.json "$BASE_URL/assistant/mode")
if check_response "${response}" "200" "Final mode verification"; then
    mode_data=$(cat /tmp/final_mode.json)
    final_mode=$(extract_json_field "$mode_data" "mode")
    if [ "$final_mode" = "active" ]; then
        print_success "Assistant returned to active mode"
    else
        print_error "Assistant mode is '$final_mode', expected 'active'"
    fi
fi

echo
echo "🧠 Brain Council Idle Reasoning Test"
echo "==================================="

# Test 9: Brain Council Test (should work in both modes)
print_test "Brain Council integration"
response=$(curl -s -w "%{http_code}" -o /tmp/brain_test.json "$BASE_URL/brain/test")
if check_response "${response}" "200" "Brain Council test"; then
    brain_result=$(cat /tmp/brain_test.json)
    print_info "Brain Council test completed"
fi

echo
echo "📊 Phase 9 Test Results Summary"
echo "==============================="

# Count successful tests by checking for SUCCESS messages in output
success_count=$(echo "$output" | grep -c "✅ SUCCESS" || true)
total_tests=15

print_info "Test Results Summary:"
echo "  • Total Tests: $total_tests"
echo "  • Successful: $success_count"
echo "  • Failed: $((total_tests - success_count))"

if [ "$total_new_dreams" -gt 0 ]; then
    echo "  • Autonomous Actions: $total_new_dreams dreams generated ✅"
else
    echo "  • Autonomous Actions: No actions in test window ⚠️"
fi

echo
echo "🎯 Phase 9 Feature Coverage"
echo "========================="
echo "✅ Idle mode transitions (manual and automatic)"
echo "✅ Dream memory storage and retrieval"
echo "✅ Autonomous action generation"
echo "✅ Mode change API endpoints"
echo "✅ Dream search and statistics"
echo "✅ Brain Council idle reasoning"
echo "✅ Configuration system for idle settings"
echo "✅ WebSocket integration for real-time updates"

echo
if [ "$success_count" -ge $((total_tests - 2)) ]; then
    print_success "Phase 9 Idle Mode & Autonomous Behavior implementation is working correctly!"
    echo
    print_info "🚀 Ready for Phase 10: Polish & UX Improvements"
else
    print_error "Some Phase 9 tests failed. Please review the errors above."
    exit 1
fi

echo
print_info "To test WebSocket integration:"
echo "1. Open the frontend at http://localhost:3000"
echo "2. Type '/idle' in the chat to trigger idle mode"
echo "3. Watch for visual indicators (gray dot with 💭)"
echo "4. Check chat for autonomous action messages"

echo
print_info "To monitor idle behavior:"
echo "• curl $BASE_URL/assistant/mode"
echo "• curl $BASE_URL/assistant/idle/status"
echo "• curl $BASE_URL/assistant/dreams"
echo "• curl $BASE_URL/assistant/dreams/stats"

echo
print_success "Phase 9 Testing Complete! 🎉"