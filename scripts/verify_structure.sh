#!/bin/bash
set -e

echo "================================="
echo "Phase 1 Structure Verification"
echo "================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Function to check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Directory exists: $1"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} Directory missing: $1"
        ((FAIL_COUNT++))
    fi
}

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} File missing: $1"
        ((FAIL_COUNT++))
    fi
}

echo -e "\n${YELLOW}Checking directories...${NC}"
check_dir "backend/app/models"
check_dir "backend/app/services"
check_dir "backend/app/api"
check_dir "backend/app/db"
check_dir "backend/app/utils"
check_dir "backend/tests"
check_dir "frontend/src/components"
check_dir "frontend/src/hooks"
check_dir "frontend/src/stores"
check_dir "frontend/src/utils"
check_dir "frontend/src/types"
check_dir "frontend/tests"
check_dir "data/personas"
check_dir "data/sprites/objects"
check_dir "data/sprites/expressions"
check_dir "data/rooms"
check_dir "docs"

echo -e "\n${YELLOW}Checking files...${NC}"
check_file "docker-compose.yml"
check_file "backend/Dockerfile"
check_file "backend/requirements.txt"
check_file "backend/app/__init__.py"
check_file "backend/app/main.py"
check_file "backend/app/api/__init__.py"
check_file "backend/app/api/health.py"
check_file "backend/app/db/__init__.py"
check_file "backend/app/db/database.py"
check_file "backend/app/db/qdrant.py"
check_file "README.md"
check_file ".gitignore"

echo -e "\n================================="
echo -e "Results: ${GREEN}${PASS_COUNT} passed${NC}, ${RED}${FAIL_COUNT} failed${NC}"
echo "================================="

if [ $FAIL_COUNT -gt 0 ]; then
    exit 1
fi