import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


class QdrantManager:
    def __init__(self):
        self.client = None
        self.collections = {
            "memories": {
                "size": 1536,  # OpenAI embedding size
                "distance": Distance.COSINE
            },
            "dreams": {
                "size": 1536,
                "distance": Distance.COSINE
            }
        }

    async def connect(self):
        try:
            self.client = QdrantClient(url=QDRANT_URL)
            logger.info(f"Connected to Qdrant at {QDRANT_URL}")
            await self.ensure_collections()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False

    async def ensure_collections(self):
        for collection_name, config in self.collections.items():
            try:
                collections = self.client.get_collections().collections
                exists = any(c.name == collection_name for c in collections)
                
                if not exists:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config["size"],
                            distance=config["distance"]
                        )
                    )
                    logger.info(f"Created collection: {collection_name}")
                else:
                    logger.info(f"Collection already exists: {collection_name}")
            except Exception as e:
                logger.error(f"Error ensuring collection {collection_name}: {e}")

    async def health_check(self) -> bool:
        try:
            if not self.client:
                return False
            # Try to get collections as a health check
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def insert_memory(
        self,
        collection: str,
        memory_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        try:
            self.client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to insert memory: {e}")
            return False

    async def search_memories(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []


# Global instance
qdrant_manager = QdrantManager()