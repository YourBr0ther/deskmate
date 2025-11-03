"""
Comprehensive tests to verify Phase 1 deliverables are complete and functional.

Phase 1 Requirements:
1. Project repository structure
2. Docker Compose configuration (FastAPI, Qdrant, PostgreSQL)
3. Basic FastAPI app with health check
4. Qdrant connection and basic operations
5. Health check endpoint returns 200
"""

import pytest
import os
from pathlib import Path
from httpx import AsyncClient
from qdrant_client import QdrantClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.qdrant import QdrantManager


class TestPhase1Structure:
    """Test that all required directories and files exist."""
    
    def test_project_structure_exists(self):
        """Verify all required directories are created."""
        base_path = Path(__file__).parent.parent.parent
        
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
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory missing: {dir_path}"
            assert full_path.is_dir(), f"Path exists but is not a directory: {dir_path}"
    
    def test_docker_files_exist(self):
        """Verify Docker configuration files exist."""
        base_path = Path(__file__).parent.parent.parent
        
        required_files = [
            "docker-compose.yml",
            "backend/Dockerfile",
            "backend/requirements.txt"
        ]
        
        for file_path in required_files:
            full_path = base_path / file_path
            assert full_path.exists(), f"File missing: {file_path}"
            assert full_path.is_file(), f"Path exists but is not a file: {file_path}"
    
    def test_core_app_files_exist(self):
        """Verify core application files exist."""
        base_path = Path(__file__).parent.parent.parent
        
        required_files = [
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
        
        for file_path in required_files:
            full_path = base_path / file_path
            assert full_path.exists(), f"File missing: {file_path}"


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test the health check endpoint functionality."""
    
    async def test_health_endpoint_exists(self, client: AsyncClient):
        """Test that health endpoint is accessible."""
        response = await client.get("/health")
        assert response.status_code == 200
    
    async def test_health_response_format(self, client: AsyncClient):
        """Test health endpoint returns correct format."""
        response = await client.get("/health")
        data = response.json()
        
        # Required fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data
        
        # Service checks
        assert "api" in data["services"]
        assert "postgres" in data["services"]
        assert "qdrant" in data["services"]
        
        # Version check
        assert data["version"] == "0.1.0"
    
    async def test_api_service_healthy(self, client: AsyncClient):
        """Test that API service reports as healthy."""
        response = await client.get("/health")
        data = response.json()
        assert data["services"]["api"] == "healthy"


@pytest.mark.asyncio
class TestDatabaseConnections:
    """Test database connectivity."""
    
    async def test_postgresql_connection(self):
        """Test that we can connect to PostgreSQL."""
        db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://deskmate:deskmate@localhost:5432/deskmate")
        engine = create_async_engine(db_url.replace("postgresql://", "postgresql+asyncpg://"))
        
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            await engine.dispose()
    
    async def test_qdrant_connection(self):
        """Test that we can connect to Qdrant."""
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url)
        
        # Should be able to get collections (even if empty)
        collections = client.get_collections()
        assert collections is not None


@pytest.mark.asyncio
class TestQdrantOperations:
    """Test Qdrant vector database operations."""
    
    async def test_qdrant_manager_initialization(self):
        """Test QdrantManager can be initialized."""
        from qdrant_client.models import Distance
        
        manager = QdrantManager()
        assert manager is not None
        assert manager.collections == {
            "memories": {"size": 1536, "distance": Distance.COSINE},
            "dreams": {"size": 1536, "distance": Distance.COSINE}
        }
    
    async def test_qdrant_manager_connect(self):
        """Test QdrantManager can connect to Qdrant."""
        manager = QdrantManager()
        success = await manager.connect()
        assert success is True
        assert manager.client is not None
    
    async def test_qdrant_collections_created(self):
        """Test that required collections are created."""
        manager = QdrantManager()
        await manager.connect()
        
        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        assert "memories" in collection_names
        assert "dreams" in collection_names
    
    async def test_qdrant_memory_operations(self):
        """Test basic memory insert and search operations."""
        manager = QdrantManager()
        await manager.connect()
        
        # Test insert
        test_vector = [0.1] * 1536  # Dummy vector
        success = await manager.insert_memory(
            collection="memories",
            memory_id="test_memory_1",
            vector=test_vector,
            payload={"content": "Test memory", "timestamp": "2025-01-01"}
        )
        assert success is True
        
        # Test search
        results = await manager.search_memories(
            collection="memories",
            query_vector=test_vector,
            limit=5
        )
        assert len(results) > 0
        assert results[0]["payload"]["content"] == "Test memory"


class TestDockerCompose:
    """Test Docker Compose configuration."""
    
    def test_docker_compose_valid(self):
        """Test that docker-compose.yml is valid YAML."""
        import yaml
        
        compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
        with open(compose_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required services
        assert "services" in config
        assert "backend" in config["services"]
        assert "postgres" in config["services"]
        assert "qdrant" in config["services"]
        
        # Check backend configuration
        backend = config["services"]["backend"]
        assert backend["ports"] == ["8000:8000"]
        assert "DATABASE_URL" in backend["environment"]
        assert "QDRANT_URL" in backend["environment"]
        
        # Check volumes
        assert "volumes" in config
        assert "postgres_data" in config["volumes"]
        assert "qdrant_data" in config["volumes"]


@pytest.mark.asyncio
class TestIntegration:
    """Test that all services work together."""
    
    async def test_health_check_with_all_services(self, client: AsyncClient):
        """Test health check when all services are running."""
        # First ensure services are initialized
        from app.db.database import init_db
        await init_db()
        
        # Then check health
        response = await client.get("/health")
        data = response.json()
        
        # In a fully integrated environment, all services should be healthy
        # Note: This may show "unhealthy" if Docker services aren't running
        assert response.status_code == 200
        assert data["status"] in ["healthy", "degraded"]
    
    async def test_api_documentation_available(self, client: AsyncClient):
        """Test that API documentation is accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200
        
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "DeskMate API"
        assert data["info"]["version"] == "0.1.0"