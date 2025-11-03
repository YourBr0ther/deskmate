#!/bin/bash
set -e

echo "================================="
echo "Phase 1 Verification Tests"
echo "================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

echo -e "\n${YELLOW}1. Starting Docker services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "\n${YELLOW}2. Waiting for services to initialize...${NC}"
sleep 10

# Check if services are running
echo -e "\n${YELLOW}3. Checking Docker services status...${NC}"
docker-compose ps

# Test health endpoint with curl
echo -e "\n${YELLOW}4. Testing health endpoint with curl...${NC}"
curl -f http://localhost:8000/health | python -m json.tool || {
    echo -e "${RED}Health check failed!${NC}"
    docker-compose logs backend
    exit 1
}

# Run pytest inside container
echo -e "\n${YELLOW}5. Running Python tests inside container...${NC}"
docker-compose exec -T backend pytest -v tests/test_phase1_complete.py || {
    echo -e "${RED}Tests failed!${NC}"
    docker-compose logs
    exit 1
}

echo -e "\n${GREEN}=================================${NC}"
echo -e "${GREEN}All Phase 1 tests passed!${NC}"
echo -e "${GREEN}=================================${NC}"

# Show service status
echo -e "\n${YELLOW}Final service status:${NC}"
docker-compose ps

echo -e "\n${YELLOW}To stop services, run:${NC} docker-compose down"