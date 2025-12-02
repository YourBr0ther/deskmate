"""
Mock fixtures for Qdrant vector database operations.

Provides:
- Mock vector embeddings
- Mock Qdrant client
- Sample memory data
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


# Vector dimension (matches common embedding models)
VECTOR_DIMENSION = 384


def deterministic_embedding(text: str, dimension: int = VECTOR_DIMENSION) -> List[float]:
    """
    Generate a deterministic embedding from text.
    Uses hash for reproducibility in tests.
    """
    # Create hash of text
    text_hash = hashlib.sha256(text.encode()).hexdigest()

    # Generate vector from hash
    vector = []
    for i in range(dimension):
        # Use different parts of the hash to generate values
        byte_idx = (i * 2) % len(text_hash)
        hex_val = text_hash[byte_idx:byte_idx + 2]
        # Convert to float in range [-1, 1]
        int_val = int(hex_val, 16) if hex_val else 0
        normalized = (int_val / 127.5) - 1.0
        vector.append(normalized)

    # Normalize the vector
    magnitude = sum(v ** 2 for v in vector) ** 0.5
    if magnitude > 0:
        vector = [v / magnitude for v in vector]

    return vector


@dataclass
class MockMemoryPoint:
    """Mock memory point (vector + payload)."""
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    score: float = 1.0


@dataclass
class MockSearchResult:
    """Mock search result from Qdrant."""
    id: str
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None


# Sample memories for testing
SAMPLE_MEMORIES = [
    {
        "id": "mem_001",
        "text": "User asked about the weather today",
        "role": "user",
        "timestamp": "2024-01-01T10:00:00Z",
        "importance": 0.5,
        "persona": "Alice"
    },
    {
        "id": "mem_002",
        "text": "I told the user it was sunny and warm",
        "role": "assistant",
        "timestamp": "2024-01-01T10:00:05Z",
        "importance": 0.5,
        "persona": "Alice"
    },
    {
        "id": "mem_003",
        "text": "User mentioned they like reading books",
        "role": "user",
        "timestamp": "2024-01-01T10:05:00Z",
        "importance": 0.7,
        "persona": "Alice"
    },
    {
        "id": "mem_004",
        "text": "I recommended 'The Great Gatsby' as a good read",
        "role": "assistant",
        "timestamp": "2024-01-01T10:05:10Z",
        "importance": 0.6,
        "persona": "Alice"
    },
]

SAMPLE_DREAMS = [
    {
        "id": "dream_001",
        "action": "move",
        "target": {"x": 10, "y": 5},
        "thought": "I should check on the plant by the window",
        "timestamp": "2024-01-01T15:00:00Z",
        "persona": "Alice"
    },
    {
        "id": "dream_002",
        "action": "interact",
        "target": "lamp",
        "thought": "It's getting dark, I should turn on the lamp",
        "timestamp": "2024-01-01T18:00:00Z",
        "persona": "Alice"
    },
]


class MockQdrantClient:
    """Mock Qdrant client for testing."""

    def __init__(self):
        self._collections: Dict[str, List[MockMemoryPoint]] = {
            "conversation_memory": [],
            "dream_memory": [],
        }
        self._initialized = False

    async def create_collection(
        self,
        collection_name: str,
        vectors_config: Any = None
    ) -> bool:
        """Create a new collection."""
        if collection_name not in self._collections:
            self._collections[collection_name] = []
        return True

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        if collection_name in self._collections:
            del self._collections[collection_name]
            return True
        return False

    async def get_collections(self) -> List[str]:
        """Get list of collections."""
        return list(self._collections.keys())

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        return collection_name in self._collections

    async def upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> bool:
        """Upsert points into collection."""
        if collection_name not in self._collections:
            self._collections[collection_name] = []

        for point in points:
            # Remove existing point with same ID
            self._collections[collection_name] = [
                p for p in self._collections[collection_name]
                if p.id != point.get("id")
            ]

            # Add new point
            new_point = MockMemoryPoint(
                id=point.get("id", f"point_{len(self._collections[collection_name])}"),
                vector=point.get("vector", deterministic_embedding(str(point))),
                payload=point.get("payload", {})
            )
            self._collections[collection_name].append(new_point)

        return True

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        with_payload: bool = True,
        with_vectors: bool = False,
        query_filter: Any = None
    ) -> List[MockSearchResult]:
        """Search for similar vectors."""
        if collection_name not in self._collections:
            return []

        points = self._collections[collection_name]

        # Calculate similarity scores (cosine similarity)
        results = []
        for point in points:
            # Simple dot product for normalized vectors
            score = sum(a * b for a, b in zip(query_vector, point.vector))

            if score >= score_threshold:
                results.append(MockSearchResult(
                    id=point.id,
                    score=score,
                    payload=point.payload if with_payload else {},
                    vector=point.vector if with_vectors else None
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:limit]

    async def delete(
        self,
        collection_name: str,
        points_selector: Any = None
    ) -> bool:
        """Delete points from collection."""
        if collection_name not in self._collections:
            return False

        if points_selector:
            # Filter out deleted points (simplified)
            if hasattr(points_selector, 'points'):
                ids_to_delete = set(points_selector.points)
                self._collections[collection_name] = [
                    p for p in self._collections[collection_name]
                    if p.id not in ids_to_delete
                ]

        return True

    async def count(self, collection_name: str) -> int:
        """Count points in collection."""
        return len(self._collections.get(collection_name, []))

    async def scroll(
        self,
        collection_name: str,
        limit: int = 100,
        offset: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> tuple:
        """Scroll through collection."""
        points = self._collections.get(collection_name, [])
        results = [
            MockSearchResult(
                id=p.id,
                score=1.0,
                payload=p.payload if with_payload else {},
                vector=p.vector if with_vectors else None
            )
            for p in points[:limit]
        ]
        next_offset = None if len(points) <= limit else str(limit)
        return results, next_offset

    def seed_memories(self, collection_name: str = "conversation_memory"):
        """Seed collection with sample memories."""
        for memory in SAMPLE_MEMORIES:
            point = MockMemoryPoint(
                id=memory["id"],
                vector=deterministic_embedding(memory["text"]),
                payload=memory
            )
            if collection_name not in self._collections:
                self._collections[collection_name] = []
            self._collections[collection_name].append(point)

    def seed_dreams(self, collection_name: str = "dream_memory"):
        """Seed collection with sample dreams."""
        for dream in SAMPLE_DREAMS:
            point = MockMemoryPoint(
                id=dream["id"],
                vector=deterministic_embedding(dream["thought"]),
                payload=dream
            )
            if collection_name not in self._collections:
                self._collections[collection_name] = []
            self._collections[collection_name].append(point)


class MockEmbeddingService:
    """Mock embedding service."""

    def __init__(self, dimension: int = VECTOR_DIMENSION):
        self.dimension = dimension
        self._call_count = 0

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        self._call_count += 1
        return deterministic_embedding(text, self.dimension)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [await self.embed_text(t) for t in texts]

    def get_call_count(self) -> int:
        """Get number of embedding calls."""
        return self._call_count


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    return MockQdrantClient()


@pytest.fixture
def mock_qdrant_with_memories():
    """Create a mock Qdrant client with seeded memories."""
    client = MockQdrantClient()
    client.seed_memories()
    return client


@pytest.fixture
def mock_qdrant_with_dreams():
    """Create a mock Qdrant client with seeded dreams."""
    client = MockQdrantClient()
    client.seed_dreams()
    return client


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    return MockEmbeddingService()


@pytest.fixture
def deterministic_embedder():
    """Return the deterministic embedding function."""
    return deterministic_embedding


@pytest.fixture
def sample_memories():
    """Return sample memory data."""
    return list(SAMPLE_MEMORIES)


@pytest.fixture
def sample_dreams():
    """Return sample dream data."""
    return list(SAMPLE_DREAMS)


@pytest.fixture
def patch_qdrant():
    """Patch Qdrant client for tests."""
    with patch("app.db.qdrant.get_qdrant_client") as mock_get_client:
        client = MockQdrantClient()
        client.seed_memories()
        mock_get_client.return_value = client
        yield client


@pytest.fixture
def patch_embedding_service():
    """Patch embedding service for tests."""
    with patch("app.services.embedding_service.EmbeddingService") as mock_service:
        service = MockEmbeddingService()
        mock_service.return_value = service
        yield service
