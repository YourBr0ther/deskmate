"""
Mock fixtures for database operations.

Provides:
- In-memory SQLite database for testing
- Mock SQLAlchemy sessions
- Sample data fixtures
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


# Sample data for testing
@dataclass
class MockAssistantState:
    """Mock assistant state data."""
    id: int = 1
    position_x: int = 5
    position_y: int = 5
    current_room: str = "living_room"
    mood: str = "neutral"
    expression: str = "default"
    energy_level: float = 1.0
    is_idle: bool = False
    holding_object_id: Optional[int] = None
    sitting_on_id: Optional[int] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MockRoomObject:
    """Mock room object data."""
    id: int = 1
    name: str = "desk"
    object_type: str = "furniture"
    position_x: int = 10
    position_y: int = 8
    width: int = 2
    height: int = 1
    is_interactive: bool = True
    is_movable: bool = False
    is_sittable: bool = False
    current_state: Dict[str, Any] = field(default_factory=dict)
    room_id: str = "living_room"


@dataclass
class MockPersona:
    """Mock persona data."""
    id: int = 1
    name: str = "Alice"
    description: str = "A friendly AI companion"
    personality: str = "Cheerful and helpful"
    first_message: str = "Hi! I'm Alice, nice to meet you!"
    scenario: str = "You are chatting with Alice in a cozy room"
    expressions: Dict[str, str] = field(default_factory=lambda: {
        "default": "/personas/alice/expressions/default.png",
        "happy": "/personas/alice/expressions/happy.png",
        "sad": "/personas/alice/expressions/sad.png"
    })


# Sample collections of mock data
MOCK_ROOM_OBJECTS = [
    MockRoomObject(id=1, name="desk", object_type="furniture", position_x=10, position_y=8),
    MockRoomObject(id=2, name="chair", object_type="furniture", position_x=12, position_y=8, is_sittable=True),
    MockRoomObject(id=3, name="lamp", object_type="decoration", position_x=10, position_y=7, is_interactive=True),
    MockRoomObject(id=4, name="book", object_type="item", position_x=11, position_y=8, is_movable=True),
    MockRoomObject(id=5, name="window", object_type="window", position_x=5, position_y=0, width=3, height=1),
]

MOCK_PERSONAS = [
    MockPersona(id=1, name="Alice", description="A friendly AI companion"),
    MockPersona(id=2, name="Bob", description="A knowledgeable assistant"),
]


class MockDatabaseSession:
    """Mock async database session."""

    def __init__(self):
        self._data: Dict[str, List[Any]] = {
            "assistant_state": [MockAssistantState()],
            "room_objects": list(MOCK_ROOM_OBJECTS),
            "personas": list(MOCK_PERSONAS),
        }
        self._committed = False
        self._rolled_back = False

    async def execute(self, query, params=None):
        """Mock execute query."""
        return MagicMock(
            scalars=MagicMock(return_value=MagicMock(
                all=MagicMock(return_value=self._data.get("room_objects", [])),
                first=MagicMock(return_value=self._data.get("room_objects", [None])[0])
            ))
        )

    async def commit(self):
        """Mock commit."""
        self._committed = True

    async def rollback(self):
        """Mock rollback."""
        self._rolled_back = True

    async def close(self):
        """Mock close."""
        pass

    async def refresh(self, obj):
        """Mock refresh."""
        pass

    def add(self, obj):
        """Mock add object to session."""
        pass

    def delete(self, obj):
        """Mock delete object from session."""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockRepository:
    """Base mock repository with common CRUD operations."""

    def __init__(self, data: List[Any] = None):
        self._data = data or []
        self._next_id = max([item.id for item in self._data], default=0) + 1

    async def get_by_id(self, id: int) -> Optional[Any]:
        """Get item by ID."""
        for item in self._data:
            if item.id == id:
                return item
        return None

    async def get_all(self) -> List[Any]:
        """Get all items."""
        return self._data

    async def create(self, item: Any) -> Any:
        """Create new item."""
        item.id = self._next_id
        self._next_id += 1
        self._data.append(item)
        return item

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Any]:
        """Update item by ID."""
        item = await self.get_by_id(id)
        if item:
            for key, value in updates.items():
                if hasattr(item, key):
                    setattr(item, key, value)
        return item

    async def delete(self, id: int) -> bool:
        """Delete item by ID."""
        item = await self.get_by_id(id)
        if item:
            self._data.remove(item)
            return True
        return False


class MockAssistantRepository(MockRepository):
    """Mock repository for assistant state."""

    def __init__(self):
        super().__init__([MockAssistantState()])

    async def get_current_state(self) -> MockAssistantState:
        """Get current assistant state."""
        return self._data[0] if self._data else None

    async def update_position(self, x: int, y: int) -> MockAssistantState:
        """Update assistant position."""
        state = await self.get_current_state()
        if state:
            state.position_x = x
            state.position_y = y
            state.last_activity = datetime.utcnow()
        return state

    async def update_mood(self, mood: str, expression: str = None) -> MockAssistantState:
        """Update assistant mood and expression."""
        state = await self.get_current_state()
        if state:
            state.mood = mood
            if expression:
                state.expression = expression
        return state

    async def set_idle(self, is_idle: bool) -> MockAssistantState:
        """Set idle state."""
        state = await self.get_current_state()
        if state:
            state.is_idle = is_idle
        return state


class MockRoomRepository(MockRepository):
    """Mock repository for room objects."""

    def __init__(self):
        super().__init__(list(MOCK_ROOM_OBJECTS))

    async def get_by_room(self, room_id: str) -> List[MockRoomObject]:
        """Get all objects in a room."""
        return [obj for obj in self._data if obj.room_id == room_id]

    async def get_at_position(self, x: int, y: int) -> Optional[MockRoomObject]:
        """Get object at specific position."""
        for obj in self._data:
            if obj.position_x <= x < obj.position_x + obj.width:
                if obj.position_y <= y < obj.position_y + obj.height:
                    return obj
        return None

    async def get_interactive_objects(self) -> List[MockRoomObject]:
        """Get all interactive objects."""
        return [obj for obj in self._data if obj.is_interactive]

    async def get_movable_objects(self) -> List[MockRoomObject]:
        """Get all movable objects."""
        return [obj for obj in self._data if obj.is_movable]

    async def update_position(self, id: int, x: int, y: int) -> Optional[MockRoomObject]:
        """Update object position."""
        return await self.update(id, {"position_x": x, "position_y": y})


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MockDatabaseSession()


@pytest.fixture
def mock_assistant_repository():
    """Create a mock assistant repository."""
    return MockAssistantRepository()


@pytest.fixture
def mock_room_repository():
    """Create a mock room repository."""
    return MockRoomRepository()


@pytest.fixture
def mock_assistant_state():
    """Create a mock assistant state."""
    return MockAssistantState()


@pytest.fixture
def mock_room_objects():
    """Create mock room objects."""
    return list(MOCK_ROOM_OBJECTS)


@pytest.fixture
def mock_personas():
    """Create mock personas."""
    return list(MOCK_PERSONAS)


@pytest.fixture
def patch_database():
    """Patch database session for tests."""
    with patch("app.db.database.get_db") as mock_get_db:
        session = MockDatabaseSession()
        mock_get_db.return_value = session

        async def async_session():
            yield session

        mock_get_db.return_value = async_session()
        yield session
