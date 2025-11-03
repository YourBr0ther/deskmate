#!/usr/bin/env python3
"""
Phase 1 verification script that checks all deliverables.
"""
import os
import sys
import json
import yaml
from pathlib import Path

def check_structure():
    """Check that all required directories and files exist."""
    print("🔍 Checking project structure...")
    
    base_path = Path(".")
    
    required_dirs = [
        "backend/app/models",
        "backend/app/services", 
        "backend/app/api",
        "backend/app/db",
        "backend/app/utils",
        "backend/tests",
        "frontend/src/components",
        "frontend/src/hooks",
        "frontend/src/stores",
        "frontend/src/utils",
        "frontend/src/types",
        "frontend/tests",
        "data/personas",
        "data/sprites/objects",
        "data/sprites/expressions",
        "data/rooms",
        "docs"
    ]
    
    required_files = [
        "docker-compose.yml",
        "backend/Dockerfile",
        "backend/requirements.txt",
        "backend/app/__init__.py",
        "backend/app/main.py",
        "backend/app/api/__init__.py",
        "backend/app/api/health.py",
        "backend/app/db/__init__.py",
        "backend/app/db/database.py",
        "backend/app/db/qdrant.py",
        "README.md",
        ".gitignore"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(dir_path)
    
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists() or not full_path.is_file():
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required directories and files exist")
    return True

def check_docker_compose():
    """Check docker-compose.yml configuration."""
    print("🔍 Checking Docker Compose configuration...")
    
    try:
        with open("docker-compose.yml", 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required services
        if "services" not in config:
            print("❌ No services defined in docker-compose.yml")
            return False
        
        required_services = ["backend", "postgres", "qdrant"]
        for service in required_services:
            if service not in config["services"]:
                print(f"❌ Missing service: {service}")
                return False
        
        # Check backend configuration
        backend = config["services"]["backend"]
        if "ports" not in backend or "8000:8000" not in backend["ports"]:
            print("❌ Backend service missing port 8000")
            return False
        
        print("✅ Docker Compose configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error checking docker-compose.yml: {e}")
        return False

def check_requirements():
    """Check that requirements.txt has necessary dependencies."""
    print("🔍 Checking requirements.txt...")
    
    try:
        with open("backend/requirements.txt", 'r') as f:
            requirements = f.read()
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "qdrant-client",
            "pytest"
        ]
        
        missing_packages = []
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages in requirements.txt: {missing_packages}")
            return False
        
        print("✅ Requirements.txt has all necessary dependencies")
        return True
        
    except Exception as e:
        print(f"❌ Error checking requirements.txt: {e}")
        return False

def check_fastapi_app():
    """Check that FastAPI app can be imported."""
    print("🔍 Checking FastAPI application...")
    
    try:
        # Check main.py structure
        with open("backend/app/main.py", 'r') as f:
            content = f.read()
        
        required_imports = [
            "from fastapi import FastAPI",
            "from app.api import health"
        ]
        
        for import_stmt in required_imports:
            if import_stmt not in content:
                print(f"❌ Missing import in main.py: {import_stmt}")
                return False
        
        # Check health.py structure
        with open("backend/app/api/health.py", 'r') as f:
            health_content = f.read()
        
        if "@router.get" not in health_content or "/health" not in health_content:
            print("❌ Health endpoint not properly defined")
            return False
        
        print("✅ FastAPI application structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error checking FastAPI app: {e}")
        return False

def main():
    """Run all verification checks."""
    print("="*50)
    print("Phase 1 Verification")
    print("="*50)
    
    checks = [
        check_structure,
        check_docker_compose,
        check_requirements,
        check_fastapi_app
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if check():
            passed += 1
        print()
    
    print("="*50)
    print(f"Results: {passed}/{total} checks passed")
    print("="*50)
    
    if passed == total:
        print("🎉 Phase 1 verification complete!")
        print("\nNext steps:")
        print("1. Run: docker-compose up -d")
        print("2. Test: curl http://localhost:8000/health")
        print("3. Ready for Phase 2!")
        return True
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)