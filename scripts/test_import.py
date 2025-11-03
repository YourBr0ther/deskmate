#!/usr/bin/env python3
"""
Simple import test to verify all modules can be imported.
"""
import sys
sys.path.append('backend')

def test_imports():
    """Test that all core modules can be imported."""
    try:
        print("Testing imports...")
        
        # Test main app
        from app.main import app
        print("✓ Main app imports successfully")
        
        # Test health API
        from app.api.health import router
        print("✓ Health API imports successfully")
        
        # Test database modules
        from app.db.database import Base, engine
        print("✓ Database module imports successfully")
        
        # Test Qdrant module
        from app.db.qdrant import QdrantManager
        print("✓ Qdrant module imports successfully")
        
        # Test that we can create a QdrantManager instance
        manager = QdrantManager()
        print("✓ QdrantManager can be instantiated")
        
        print("\nAll imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)