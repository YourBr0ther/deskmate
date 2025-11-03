#!/bin/bash
set -e

echo "================================="
echo "Basic Phase 1 Tests"
echo "================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is available
echo -e "\n${YELLOW}Checking Docker availability...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed or not in PATH${NC}"
    echo "Please install Docker to run the full test suite"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not available${NC}"
    echo "Please install Docker Compose to run the full test suite"
    exit 1
fi

echo -e "${GREEN}Docker and Docker Compose are available${NC}"

# Validate docker-compose.yml
echo -e "\n${YELLOW}Validating docker-compose.yml...${NC}"
docker compose config > /dev/null 2>&1 || {
    echo -e "${RED}docker-compose.yml is invalid${NC}"
    exit 1
}
echo -e "${GREEN}docker-compose.yml is valid${NC}"

# Check if we can build the backend image
echo -e "\n${YELLOW}Testing Docker build...${NC}"
cd backend
docker build -t deskmate-backend-test . || {
    echo -e "${RED}Failed to build backend Docker image${NC}"
    exit 1
}
cd ..
echo -e "${GREEN}Backend Docker image builds successfully${NC}"

echo -e "\n${GREEN}=================================${NC}"
echo -e "${GREEN}Basic tests passed!${NC}"
echo -e "${GREEN}=================================${NC}"
echo -e "\nTo run full integration tests with services:"
echo -e "  ${YELLOW}docker-compose up -d${NC}"
echo -e "  ${YELLOW}curl http://localhost:8000/health${NC}"