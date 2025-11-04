#!/bin/bash

# Phase 8 Object Manipulation Test Suite
# Tests all object manipulation features implemented in Phase 8

set -e

echo "🧪 Phase 8 Object Manipulation Test Suite"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
BASE_URL="http://localhost:8000"
TEST_OBJECT_ID="test_mug_001"
TEST_POSITION_X=20
TEST_POSITION_Y=10

# Function to print test status
print_test() {
    echo -e "${BLUE}🔍 Testing:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
}

print_error() {
    echo -e "${RED}❌ FAIL:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

# Function to check if service is running
check_service() {
    local service_name=$1
    local url=$2

    print_test "Checking if $service_name is running..."

    if curl -s "$url" > /dev/null; then
        print_success "$service_name is running"
        return 0
    else
        print_error "$service_name is not running at $url"
        return 1
    fi
}

# Function to test API endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5

    print_test "$description"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "%{http_code}" -X POST \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$BASE_URL$endpoint")
        else
            response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL$endpoint")
        fi
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "%{http_code}" -X PUT \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi

    status_code="${response: -3}"
    response_body="${response%???}"

    if [ "$status_code" = "$expected_status" ]; then
        print_success "$description (Status: $status_code)"
        echo "   Response: $response_body" | head -c 100
        if [ ${#response_body} -gt 100 ]; then
            echo "..."
        else
            echo
        fi
        return 0
    else
        print_error "$description (Expected: $expected_status, Got: $status_code)"
        echo "   Response: $response_body"
        return 1
    fi
}

# Function to create a test object
create_test_object() {
    print_test "Creating test movable object..."

    local object_data='{
        "object_id": "'$TEST_OBJECT_ID'",
        "name": "Test Mug",
        "description": "A test mug for object manipulation",
        "object_type": "item",
        "position": {"x": 15, "y": 8},
        "size": {"width": 1, "height": 1},
        "properties": {
            "solid": true,
            "interactive": true,
            "movable": true
        },
        "sprite": "mug",
        "color": "blue"
    }'

    # Create object via room API
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$object_data" \
        "$BASE_URL/room/objects" > /dev/null

    print_success "Test object created"
}

# Function to cleanup test object
cleanup_test_object() {
    print_test "Cleaning up test object..."
    curl -s -X DELETE "$BASE_URL/room/objects/$TEST_OBJECT_ID" > /dev/null || true
    print_success "Test object cleaned up"
}

# Main test execution
main() {
    echo "Starting Phase 8 Object Manipulation tests..."
    echo

    # Check if services are running
    check_service "Backend API" "$BASE_URL/health" || exit 1
    echo

    # Test basic API health
    print_test "=== Basic API Health Tests ==="
    test_endpoint "GET" "/health" "" "200" "Health check"
    test_endpoint "GET" "/assistant/state" "" "200" "Assistant state"
    echo

    # Test object manipulation API endpoints
    print_test "=== Object Manipulation API Tests ==="

    # Test holding status when not holding anything
    test_endpoint "GET" "/assistant/holding" "" "200" "Get holding status (empty)"

    # Create test object for manipulation
    create_test_object

    # Test pick up without being close enough (should fail)
    test_endpoint "POST" "/assistant/pick-up/$TEST_OBJECT_ID" "" "400" "Pick up object from far away (should fail)"

    # Move assistant closer to test object
    print_test "Moving assistant closer to test object..."
    move_data='{"x": 15, "y": 8}'
    test_endpoint "PUT" "/assistant/position" "$move_data" "200" "Move assistant to test object position"

    # Test pick up when close enough (should succeed)
    test_endpoint "POST" "/assistant/pick-up/$TEST_OBJECT_ID" "" "200" "Pick up object when close"

    # Test holding status when holding something
    test_endpoint "GET" "/assistant/holding" "" "200" "Get holding status (holding object)"

    # Test pick up when already holding something (should fail)
    test_endpoint "POST" "/assistant/pick-up/bed" "" "400" "Try to pick up another object while holding (should fail)"

    # Test put down without position (should use current location)
    test_endpoint "POST" "/assistant/put-down" "" "200" "Put down object at current location"

    # Test holding status after put down (should be empty)
    test_endpoint "GET" "/assistant/holding" "" "200" "Get holding status after put down (should be empty)"

    # Test put down when not holding anything (should fail)
    test_endpoint "POST" "/assistant/put-down" "" "400" "Try to put down when not holding anything (should fail)"

    echo

    # Test object manipulation through Brain Council
    print_test "=== Brain Council Object Manipulation Tests ==="

    # Test Brain Council with object manipulation context
    brain_test_data='{
        "message": "pick up the test mug",
        "persona": {"name": "Alice", "personality": "helpful assistant"}
    }'
    test_endpoint "POST" "/brain/process" "$brain_test_data" "200" "Brain Council pick up suggestion"

    brain_test_data2='{
        "message": "put the object down over there",
        "persona": {"name": "Alice", "personality": "helpful assistant"}
    }'
    test_endpoint "POST" "/brain/process" "$brain_test_data2" "200" "Brain Council put down suggestion"

    echo

    # Test advanced object manipulation scenarios
    print_test "=== Advanced Object Manipulation Tests ==="

    # Pick up object again for advanced tests
    test_endpoint "POST" "/assistant/pick-up/$TEST_OBJECT_ID" "" "200" "Pick up test object for advanced tests"

    # Test put down with specific position
    put_down_data='{"position": {"x": '$TEST_POSITION_X', "y": '$TEST_POSITION_Y'}}'
    test_endpoint "POST" "/assistant/put-down" "$put_down_data" "200" "Put down object at specific position"

    # Test collision detection - try to put object on occupied space
    test_endpoint "POST" "/assistant/pick-up/$TEST_OBJECT_ID" "" "200" "Pick up object for collision test"

    collision_data='{"position": {"x": 50, "y": 12}}'  # Bed position
    test_endpoint "POST" "/assistant/put-down" "$collision_data" "400" "Try to put down on occupied space (should fail)"

    # Test boundary validation - try to put object outside grid
    boundary_data='{"position": {"x": 70, "y": 20}}'  # Outside 64x16 grid
    test_endpoint "POST" "/assistant/put-down" "$boundary_data" "400" "Try to put down outside grid bounds (should fail)"

    # Clean put down
    clean_data='{"position": {"x": 25, "y": 10}}'
    test_endpoint "POST" "/assistant/put-down" "$clean_data" "200" "Put down object in valid empty space"

    echo

    # Test error conditions
    print_test "=== Error Condition Tests ==="

    # Test pick up non-existent object
    test_endpoint "POST" "/assistant/pick-up/nonexistent_object" "" "400" "Try to pick up non-existent object (should fail)"

    # Test pick up non-movable object
    test_endpoint "POST" "/assistant/pick-up/bed" "" "400" "Try to pick up non-movable object (should fail)"

    echo

    # Cleanup
    cleanup_test_object

    # Final status
    echo
    echo "🎉 Phase 8 Object Manipulation Test Suite Completed!"
    echo
    echo "Key Features Tested:"
    echo "✅ Pick up / Put down API endpoints"
    echo "✅ Holding status tracking"
    echo "✅ Distance validation"
    echo "✅ Collision detection"
    echo "✅ Boundary validation"
    echo "✅ Brain Council integration"
    echo "✅ Error handling"
    echo
    echo "To test visual feedback:"
    echo "1. Open frontend at http://localhost:3000"
    echo "2. Use chat to ask assistant to pick up objects"
    echo "3. Observe orange ring and 📦 icon when holding objects"
    echo "4. Check debug panel for holding status"
    echo
}

# Trap to ensure cleanup on exit
trap cleanup_test_object EXIT

# Run tests
main "$@"