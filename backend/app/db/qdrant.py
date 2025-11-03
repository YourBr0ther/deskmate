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

    async def clear_collection(self, collection: str) -> bool:
        """Clear all points from a collection."""
        try:
            # Delete the collection and recreate it (fastest way to clear)
            self.client.delete_collection(collection_name=collection)

            # Recreate the collection
            if collection in self.collections:
                config = self.collections[collection]
                self.client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=config["size"],
                        distance=config["distance"]
                    )
                )
                logger.info(f"Cleared and recreated collection: {collection}")
                return True
            else:
                logger.error(f"Unknown collection: {collection}")
                return False
        except Exception as e:
            logger.error(f"Failed to clear collection {collection}: {e}")
            return False

    async def clear_all_collections(self) -> bool:
        """Clear all conversation data from all collections."""
        try:
            success = True
            for collection_name in self.collections.keys():
                if not await self.clear_collection(collection_name):
                    success = False
            return success
        except Exception as e:
            logger.error(f"Failed to clear all collections: {e}")
            return False

    async def delete_persona_memories(self, persona_name: str) -> bool:
        """Delete all memories for a specific persona."""
        try:
            # We need to scroll through and delete points with matching persona_name
            # This is more complex than clearing all, so we'll use the filter approach
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="persona_name",
                        match=MatchValue(value=persona_name)
                    )
                ]
            )

            # Delete from memories collection
            result = self.client.delete(
                collection_name="memories",
                points_selector=filter_condition
            )

            logger.info(f"Deleted memories for persona: {persona_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete persona memories: {e}")
            return False


# Global instance
qdrant_manager = QdrantManager()