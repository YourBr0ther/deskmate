# DeskMate Testing Guide

This document describes the testing architecture, strategies, and commands for the DeskMate project.

## Overview

DeskMate uses a comprehensive testing strategy covering:
- **Backend**: pytest with pytest-asyncio for Python async testing
- **Frontend**: Jest with React Testing Library for TypeScript/React testing
- **Integration**: End-to-end flow tests for critical paths

### Coverage Targets

| Component | Target Coverage |
|-----------|----------------|
| Backend Services | 85% |
| Backend APIs | 80% |
| Frontend Stores | 90% |
| Frontend Hooks | 85% |
| Frontend Components | 75% |
| **Overall** | **>80%** |

## Quick Start

### Running All Tests

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests
cd frontend
npm run test

# With coverage
cd backend && pytest --cov=app --cov-report=html
cd frontend && npm run test:coverage
```

## Backend Testing

### Directory Structure

```
backend/tests/
├── conftest.py              # Shared fixtures
├── fixtures/
│   ├── mock_llm.py          # LLM response mocks
│   ├── mock_database.py     # Database session mocks
│   └── mock_qdrant.py       # Vector search mocks
├── services/
│   ├── test_llm_manager.py
│   ├── test_embedding_service.py
│   ├── test_room_service.py
│   ├── test_assistant_service.py
│   ├── test_idle_controller.py
│   └── test_dream_memory.py
├── api/
│   ├── test_chat_api.py
│   ├── test_assistant_api.py
│   ├── test_room_api.py
│   ├── test_conversation_api.py
│   └── test_personas_api.py
└── integration/
    ├── test_full_chat_flow.py
    └── test_idle_mode_flow.py
```

### Key Fixtures

#### Database Mocking

```python
# conftest.py
@pytest.fixture
def mock_db_session():
    """In-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

#### LLM Mocking

```python
# fixtures/mock_llm.py
@pytest.fixture
def mock_llm_response():
    return {
        "response": "Mock response",
        "model": "gpt-4o-mini",
        "provider": "nano_gpt",
        "tokens": {"prompt": 50, "completion": 20}
    }
```

#### Async Testing Pattern

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_async_function():
    with patch('app.services.llm_manager.LLMManager') as mock_class:
        mock_instance = AsyncMock()
        mock_instance.generate_response.return_value = {"response": "test"}
        mock_class.return_value = mock_instance

        result = await some_async_function()
        assert result is not None
```

### Running Backend Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/services/test_llm_manager.py -v

# Specific test
pytest tests/services/test_llm_manager.py::test_generate_response -v

# With coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Coverage with threshold
pytest --cov=app --cov-fail-under=80

# Parallel execution
pytest -n auto

# Integration tests only
pytest tests/integration/ -v
```

## Frontend Testing

### Directory Structure

```
frontend/src/
├── setupTests.ts                    # Jest setup
├── test-utils/
│   ├── renderWithProviders.tsx      # Custom render
│   ├── mockWebSocket.ts             # WebSocket mock
│   └── mockApi.ts                   # API mocks
├── stores/__tests__/
│   ├── spatialStore.test.ts
│   ├── chatStore.test.ts
│   ├── personaStore.test.ts
│   └── settingsStore.test.ts
├── hooks/__tests__/
│   ├── useWebSocketIntegration.test.ts
│   ├── useFloorPlanManager.test.ts
│   ├── useRoomNavigation.test.ts
│   ├── useDeviceDetection.test.ts
│   ├── useMessageCleanup.test.ts
│   ├── useAssistantAnimation.test.ts
│   └── useTouchGestures.test.ts
└── components/
    ├── Chat/__tests__/
    │   ├── ChatWindow.test.tsx
    │   ├── ChatInput.test.tsx
    │   └── MessageList.test.tsx
    ├── Settings/__tests__/
    │   └── SettingsPanel.test.tsx
    ├── ErrorBoundary/__tests__/
    │   └── ErrorBoundary.test.tsx
    └── __tests__/
        ├── StatusIndicators.test.tsx
        └── ExpressionDisplay.test.tsx
```

### Key Testing Patterns

#### Testing Zustand Stores

```typescript
import { renderHook, act } from '@testing-library/react';
import { useChatStore } from '../chatStore';

describe('ChatStore', () => {
  beforeEach(() => {
    // Reset store state
    useChatStore.setState({
      messages: [],
      isConnected: false,
    });
  });

  it('should add message', () => {
    act(() => {
      useChatStore.getState().addMessage({
        id: '1',
        content: 'Hello',
        role: 'user',
      });
    });

    expect(useChatStore.getState().messages).toHaveLength(1);
  });
});
```

#### Testing React Hooks

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocketIntegration } from '../useWebSocketIntegration';

// Mock the WebSocket service
jest.mock('../../services/websocketService', () => ({
  websocketService: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    send: jest.fn(),
  },
}));

describe('useWebSocketIntegration', () => {
  it('should auto-connect by default', async () => {
    const { result } = renderHook(() => useWebSocketIntegration());

    await waitFor(() => {
      expect(websocketService.connect).toHaveBeenCalled();
    });
  });
});
```

#### Testing React Components

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInput from '../ChatInput';

// Mock stores
jest.mock('../../../stores/chatStore', () => ({
  useChatStore: () => ({
    currentMessage: '',
    isConnected: true,
    sendMessage: jest.fn(),
    setCurrentMessage: jest.fn(),
  }),
}));

describe('ChatInput', () => {
  it('should send message on Enter', async () => {
    render(<ChatInput />);

    const textarea = screen.getByRole('textbox');
    await userEvent.type(textarea, 'Hello');
    fireEvent.keyPress(textarea, { key: 'Enter' });

    expect(mockSendMessage).toHaveBeenCalled();
  });
});
```

### Running Frontend Tests

```bash
# All tests
npm run test

# Watch mode
npm run test -- --watch

# Specific file
npm run test -- ChatInput.test.tsx

# With coverage
npm run test:coverage

# Coverage report
npm run test:coverage -- --coverageReporters=html
```

## Mock Strategies

### Backend Mocks

| External Service | Mock Strategy |
|-----------------|---------------|
| PostgreSQL | In-memory SQLite via SQLAlchemy |
| Qdrant | Mock QdrantClient with AsyncMock |
| Nano-GPT API | Mocked HTTP responses |
| Ollama | Mocked local API responses |
| WebSocket | Mock connection handlers |

### Frontend Mocks

| Service | Mock Strategy |
|---------|---------------|
| WebSocket | Custom MockWebSocket class |
| Fetch API | jest.fn() with resolved values |
| localStorage | In-memory mock object |
| window.matchMedia | Custom mock implementation |
| requestAnimationFrame | jest.fn() with frame simulation |

## Integration Tests

### Full Chat Flow

Tests the complete pipeline:
1. User sends message via WebSocket
2. Brain Council processes message
3. Memory is stored in Qdrant
4. Response is generated via LLM
5. Actions are executed if needed
6. Response is sent back via WebSocket

```bash
pytest tests/integration/test_full_chat_flow.py -v
```

### Idle Mode Flow

Tests autonomous behavior:
1. Inactivity timeout detection
2. Idle mode activation
3. Autonomous action generation
4. Dream memory storage
5. Mode transition on user input

```bash
pytest tests/integration/test_idle_mode_flow.py -v
```

## Test Data

### Backend Test Data

Located in `backend/tests/fixtures/`:
- `mock_personas.json` - Sample persona data
- `mock_room_objects.json` - Room object configurations
- `mock_chat_history.json` - Conversation samples

### Frontend Test Data

Defined inline in test files as mock objects.

## Continuous Integration

### GitHub Actions (Future)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest --cov=app --cov-fail-under=80

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test:coverage
```

## Debugging Tests

### Backend

```bash
# Run with verbose output
pytest -v -s tests/services/test_llm_manager.py

# Run with print statements visible
pytest -v --capture=no

# Run with pdb on failure
pytest --pdb

# Run specific test with debugging
pytest tests/api/test_chat_api.py::test_send_message -v -s
```

### Frontend

```bash
# Debug mode
npm run test -- --debug

# Verbose output
npm run test -- --verbose

# Run single test file
npm run test -- stores/chatStore.test.ts
```

## Writing Good Tests

### Backend Guidelines

1. **Use fixtures** for common setup
2. **Mock external services** (database, LLM, vector DB)
3. **Test error cases** explicitly
4. **Use `@pytest.mark.asyncio`** for async tests
5. **Verify mock calls** with `assert_called_with()`

### Frontend Guidelines

1. **Test user behavior**, not implementation
2. **Use `userEvent`** over `fireEvent` for realistic interactions
3. **Mock at service boundaries** (API calls, WebSocket)
4. **Test accessibility** with role queries
5. **Clean up state** between tests with `beforeEach`

## Troubleshooting

### Common Issues

**Tests hanging on async operations:**
```python
# Add timeout to async tests
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_slow_operation():
    ...
```

**Store state leaking between tests:**
```typescript
beforeEach(() => {
  // Reset to initial state
  useStore.setState(initialState);
});
```

**Mock not being applied:**
```typescript
// Ensure mock is declared before imports
jest.mock('../../services/api');
import { useMyHook } from '../useMyHook';
```

## Coverage Reports

### Viewing Reports

```bash
# Backend - generates HTML report in htmlcov/
cd backend && pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend - generates report in coverage/
cd frontend && npm run test:coverage
open coverage/lcov-report/index.html
```

### Coverage Thresholds

Configured in:
- Backend: `pytest.ini`
- Frontend: `jest.config.js`

```javascript
// jest.config.js
coverageThreshold: {
  global: {
    branches: 70,
    functions: 75,
    lines: 80,
    statements: 80,
  },
},
```
