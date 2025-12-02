# DeskMate Developer Guide

This guide provides comprehensive technical documentation for developers working with DeskMate. It covers architecture, APIs, development workflows, and contribution guidelines.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Environment](#development-environment)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [Brain Council System](#brain-council-system)
6. [API Reference](#api-reference)
7. [Database Design](#database-design)
8. [Testing Framework](#testing-framework)
9. [Deployment](#deployment)
10. [Contributing](#contributing)

## Architecture Overview

### System Design

DeskMate follows a modern microservices architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (TypeScript)                                    │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐│
│  │  Grid Canvas         │  │  Chat Interface                  ││
│  │  (Room Renderer)     │  │  - WebSocket Client              ││
│  │  - Zustand State     │  │  - Message History               ││
│  │  - React DnD         │  │  - Settings Panel                ││
│  └──────────────────────┘  └──────────────────────────────────┘│
│                 ▲                          │                     │
│                 │ WebSocket                │ REST API            │
│                 ▼                          ▼                     │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│  FastAPI Backend (Python)                                      │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ WebSocket       │  │ LLM Router   │  │ Brain Council    │ │
│  │ Manager         │  │ - Nano-GPT   │  │ - 5 Specialists  │ │
│  │                 │  │ - Ollama     │  │ - Reasoning      │ │
│  └─────────────────┘  └──────────────┘  └──────────────────┘ │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Action Executor │  │ Room Service │  │ Memory Service   │ │
│  │ - Pathfinding   │  │ - Objects    │  │ - Vector Search  │ │
│  │ - Validation    │  │ - Physics    │  │ - Context Build  │ │
│  └─────────────────┘  └──────────────┘  └──────────────────┘ │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│  Data Layer                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ PostgreSQL   │  │ Qdrant       │  │ File System        │  │
│  │ - Objects    │  │ - Memories   │  │ - Personas         │  │
│  │ - Assistant  │  │ - Embeddings │  │ - Assets           │  │
│  │ - Metadata   │  │ - Semantic   │  │ - Configurations   │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Core Components

#### Brain Council System
Multi-perspective AI reasoning with 5 specialized council members:
1. **Personality Core**: Character consistency and emotional responses
2. **Memory Keeper**: Context retrieval and conversation history
3. **Spatial Reasoner**: Room layout and object relationship understanding
4. **Action Planner**: Movement and interaction planning
5. **Validator**: Action feasibility and safety checking

#### Action Execution Pipeline
```python
User Input → Brain Council → Action Planning → Validation → Execution → Feedback
```

#### Real-time Communication
- WebSocket connections for low-latency chat and commands
- RESTful APIs for configuration and data management
- Event-driven updates for room state synchronization

## Development Environment

### Prerequisites

```bash
# Required tools
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

# Python dependencies
- FastAPI 0.115+
- uvicorn[standard]
- SQLAlchemy 1.4+
- qdrant-client
- langchain

# Node.js dependencies
- React 18+
- TypeScript 4.9+
- Zustand 4.4+
- TailwindCSS 3.3+
```

### Quick Development Setup

```bash
# Clone repository
git clone https://github.com/YourBr0ther/deskmate.git
cd deskmate

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start databases
docker-compose up -d deskmate-postgres deskmate-qdrant

# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm start
```

### Development Tools

#### Code Quality
```bash
# Python linting and formatting
ruff check .
ruff format .
mypy app/

# TypeScript checking
npm run typecheck
npm run lint

# Pre-commit hooks
pre-commit install
```

#### Testing
```bash
# Backend tests
pytest -v --cov=app tests/

# Frontend tests
npm test
npm run test:coverage

# End-to-end tests
npm run test:e2e
```

## Backend Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py              # Configuration management
│   ├── models/                # Data models
│   │   ├── assistant.py
│   │   ├── room.py
│   │   ├── persona.py
│   │   └── memory.py
│   ├── services/              # Business logic
│   │   ├── brain_council.py   # AI reasoning system
│   │   ├── action_executor.py # Action processing
│   │   ├── llm_manager.py     # LLM integration
│   │   ├── room_service.py    # Room management
│   │   ├── assistant_service.py
│   │   ├── conversation_memory.py
│   │   └── pathfinding.py
│   ├── api/                   # API endpoints
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── assistant.py
│   │   │   ├── room.py
│   │   │   └── brain_council.py
│   │   └── websocket.py
│   ├── db/                    # Database connections
│   │   ├── database.py        # PostgreSQL
│   │   └── qdrant.py          # Vector database
│   └── utils/                 # Utilities
│       ├── logging.py
│       ├── embeddings.py
│       └── image.py
├── tests/                     # Test suite
├── requirements.txt
└── Dockerfile
```

### Key Services

#### Brain Council Service
```python
class BrainCouncil:
    """Multi-perspective AI reasoning system."""

    async def process_user_message(
        self,
        user_message: str,
        persona_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process message through 5-member council."""

        # Gather context
        assistant_state = await assistant_service.get_state()
        room_state = await room_service.get_state()
        memories = await conversation_memory.search_relevant(user_message)

        # Council deliberation
        council_response = await self._run_council_session({
            "user_message": user_message,
            "assistant_state": assistant_state,
            "room_state": room_state,
            "memories": memories,
            "persona_context": persona_context
        })

        # Execute actions
        actions = council_response.get("actions", [])
        for action in actions:
            await action_executor.execute_action(action)

        return {
            "response": council_response["response_message"],
            "actions": actions,
            "mood": council_response["personality_core"]["mood"],
            "confidence": council_response["validator"]["confidence"]
        }
```

#### Action Executor
```python
class ActionExecutor:
    """Executes actions generated by Brain Council."""

    async def execute_action(self, action: Dict[str, Any]) -> ActionResult:
        """Execute a single action with validation."""

        # Validate action structure
        if not self._validate_action_format(action):
            return ActionResult(success=False, message="Invalid action format")

        action_type = action.get("type")

        if action_type == "move":
            return await self._execute_movement(action)
        elif action_type == "interact":
            return await self._execute_interaction(action)
        elif action_type == "state_change":
            return await self._execute_state_change(action)
        else:
            return ActionResult(success=False, message=f"Unknown action type: {action_type}")

    async def _execute_movement(self, action: Dict) -> ActionResult:
        """Execute movement action with pathfinding."""
        target = action["target"]

        # Find path using A* algorithm
        path = await pathfinding_service.find_path(
            start=assistant_service.get_position(),
            goal=Position(x=target["x"], y=target["y"])
        )

        if not path:
            return ActionResult(success=False, message="No valid path found")

        # Execute movement
        await assistant_service.move_along_path(path)
        return ActionResult(success=True, message=f"Moved to ({target['x']}, {target['y']})")
```

#### LLM Manager
```python
class LLMManager:
    """Manages multiple LLM providers."""

    def __init__(self):
        self.providers = {
            "nano_gpt": NanoGPTProvider(),
            "ollama": OllamaProvider()
        }

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = None,
        provider: str = None
    ) -> str:
        """Get chat completion from specified provider."""

        # Auto-select provider if not specified
        if not provider:
            provider = self._select_best_provider(messages, model)

        provider_instance = self.providers[provider]
        return await provider_instance.complete(messages, model)

    def _select_best_provider(self, messages: List[ChatMessage], model: str) -> str:
        """Select optimal provider based on context."""
        # Complex requests → Nano-GPT
        # Simple requests → Ollama
        # Idle mode → Ollama lightweight models

        total_tokens = sum(len(msg.content.split()) for msg in messages)

        if total_tokens > 500 or any("complex" in msg.content for msg in messages):
            return "nano_gpt"
        return "ollama"
```

### API Design

#### RESTful Endpoints

```python
# app/api/routes/brain_council.py
@router.post("/process")
async def process_message(request: ProcessMessageRequest):
    """Process user message through Brain Council."""

    result = await brain_council.process_user_message(
        user_message=request.message,
        persona_context=request.persona_context
    )

    return BrainCouncilResponse(**result)

@router.post("/analyze")
async def analyze_context(request: AnalyzeContextRequest):
    """Analyze current context without executing actions."""

    analysis = await brain_council.analyze_current_context(
        include_memory=request.include_memory,
        persona_name=request.persona_name
    )

    return ContextAnalysisResponse(**analysis)

@router.get("/test")
async def test_brain_council():
    """Test Brain Council functionality."""

    test_result = await brain_council.run_system_test()
    return {"status": "ok", "test_results": test_result}
```

#### WebSocket Implementation

```python
# app/api/websocket.py
class WebSocketManager:
    """Manages WebSocket connections and message routing."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def handle_message(self, message: dict, websocket: WebSocket):
        """Route incoming messages to appropriate handlers."""

        message_type = message.get("type")

        if message_type == "chat":
            await self._handle_chat_message(message, websocket)
        elif message_type == "assistant_move":
            await self._handle_move_command(message, websocket)
        elif message_type == "status_request":
            await self._handle_status_request(websocket)
        else:
            await self._send_error(websocket, f"Unknown message type: {message_type}")

    async def _handle_chat_message(self, message: dict, websocket: WebSocket):
        """Process chat messages through Brain Council."""

        # Send typing indicator
        await self.send_personal_message({
            "type": "typing",
            "isTyping": True
        }, websocket)

        try:
            # Process through Brain Council
            result = await brain_council.process_user_message(
                user_message=message["content"],
                persona_context=message.get("persona_context")
            )

            # Send response
            await self.send_personal_message({
                "type": "chat_response",
                "content": result["response"],
                "actions": result["actions"],
                "mood": result["mood"],
                "timestamp": datetime.now().isoformat()
            }, websocket)

            # Broadcast state updates to all clients
            await self.broadcast_assistant_update(result.get("assistant_state"))

        except Exception as e:
            await self._send_error(websocket, f"Error processing message: {str(e)}")
        finally:
            # Stop typing indicator
            await self.send_personal_message({
                "type": "typing",
                "isTyping": False
            }, websocket)
```

### Database Integration

#### PostgreSQL Models
```python
# app/models/assistant.py
class Assistant(Base):
    """Assistant state model."""

    __tablename__ = "assistants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    position_x = Column(Integer, default=32)
    position_y = Column(Integer, default=8)
    facing = Column(String, default="right")
    current_action = Column(String, default="idle")
    mood = Column(String, default="neutral")
    expression = Column(String, default="neutral.png")
    energy = Column(Float, default=1.0)
    status = Column(String, default="active")
    holding_object_id = Column(String, nullable=True)
    sitting_on_object_id = Column(String, nullable=True)
    last_action_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Qdrant Vector Storage
```python
# app/services/conversation_memory.py
class ConversationMemory:
    """Vector-based conversation memory system."""

    async def store_memory(self, content: str, persona_name: str, metadata: dict):
        """Store conversation memory with vector embedding."""

        # Generate embedding
        embedding = await self._generate_embedding(content)

        # Create memory entry
        memory_entry = {
            "id": str(uuid.uuid4()),
            "content": content,
            "persona_name": persona_name,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }

        # Store in Qdrant
        await qdrant_client.upsert(
            collection_name="conversation_memory",
            points=[{
                "id": memory_entry["id"],
                "vector": embedding,
                "payload": memory_entry
            }]
        )

    async def search_relevant_memories(
        self,
        query: str,
        persona_name: str,
        limit: int = 5
    ) -> List[Dict]:
        """Search for relevant memories using vector similarity."""

        query_embedding = await self._generate_embedding(query)

        search_results = await qdrant_client.search(
            collection_name="conversation_memory",
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {"key": "persona_name", "match": {"value": persona_name}}
                ]
            },
            limit=limit
        )

        return [
            {
                "content": result.payload["content"],
                "timestamp": result.payload["timestamp"],
                "relevance": result.score,
                "metadata": result.payload["metadata"]
            }
            for result in search_results
        ]
```

## Frontend Development

### Project Structure

```
frontend/src/
├── components/
│   ├── FloorPlan/
│   │   ├── FloorPlanContainer.tsx  # Floor plan wrapper
│   │   ├── TopDownRenderer.tsx     # SVG-based room rendering
│   │   ├── FloorPlanSelector.tsx   # Floor plan selection
│   │   └── MobileFloorPlan.tsx     # Mobile-specific view
│   ├── Layout/
│   │   ├── DesktopLayout.tsx       # Desktop layout (70/30 split)
│   │   ├── TabletLayout.tsx        # Tablet layout
│   │   ├── MobileLayout.tsx        # Mobile layout with floating chat
│   │   └── FloorPlanLayout.tsx     # Base layout component
│   ├── Chat/
│   │   ├── ChatWindow.tsx     # Main chat interface
│   │   ├── MessageList.tsx    # Message history
│   │   ├── ChatInput.tsx      # Input field
│   │   └── ModelSelector.tsx  # AI model selection
│   ├── Settings/
│   │   └── SettingsPanel.tsx  # Configuration UI
│   └── TimeDisplay.tsx        # Real-time clock
├── stores/
│   ├── spatialStore.ts        # Unified state (rooms, objects, assistant)
│   ├── chatStore.ts           # Chat state management
│   ├── personaStore.ts        # Persona management
│   └── settingsStore.ts       # User settings
├── hooks/
│   ├── useWebSocketIntegration.ts  # WebSocket communication
│   ├── useAssistantAnimation.ts    # Movement animations
│   ├── useRoomNavigation.ts        # Multi-room navigation
│   ├── useDeviceDetection.ts       # Device type detection
│   ├── useFloorPlanManager.ts      # Floor plan state
│   └── useTouchGestures.ts         # Touch gesture handling
├── types/
│   ├── room.ts               # Room-related types
│   ├── chat.ts               # Chat types
│   └── persona.ts            # Persona types
└── utils/
    ├── api.ts                # API utilities
    └── pathfinding.ts        # Client-side pathfinding
```

### State Management with Zustand

#### Spatial Store (Unified State Management)
```typescript
// stores/spatialStore.ts
interface SpatialState {
  // Floor plan data
  currentFloorPlan: FloorPlan | null;
  rooms: Room[];

  // Room entities
  furniture: FurnitureItem[];
  assistant: AssistantState;
  storageItems: StorageItem[];

  // Interaction state
  selectedFurnitureId: string | null;
  hoveredRoomId: string | null;

  // Actions
  setFloorPlan: (floorPlan: FloorPlan) => void;
  setAssistant: (assistant: Partial<AssistantState>) => void;
  updateFurniture: (id: string, updates: Partial<FurnitureItem>) => void;
  addFurniture: (furniture: FurnitureItem) => void;
  removeFurniture: (id: string) => void;

  // Navigation
  navigateToRoom: (roomId: string) => void;
  transitionThroughDoorway: (doorwayId: string) => void;
}

export const useSpatialStore = create<SpatialState>()(
  immer((set, get) => ({
    // Initial state
    currentFloorPlan: null,
    rooms: [],
    furniture: [],
    assistant: {
      position: { x: 400, y: 300 },  // Continuous coordinates
      facing: 'right',
      currentAction: 'idle',
      mood: 'neutral',
      expression: 'neutral.png',
      mode: 'active',
      energy: 0.8,
      holdingObjectId: null,
      sittingOnObjectId: null,
      currentRoomId: null,
    },
    storageItems: [],
    selectedFurnitureId: null,
    hoveredRoomId: null,

    // Actions
    setFloorPlan: (floorPlan) =>
      set((state) => {
        state.currentFloorPlan = floorPlan;
        state.rooms = floorPlan.rooms;
        state.furniture = floorPlan.furniture;
      }),

    setAssistant: (updates) =>
      set((state) => {
        Object.assign(state.assistant, updates);
      }),

    updateFurniture: (id, updates) =>
      set((state) => {
        const item = state.furniture.find(f => f.id === id);
        if (item) Object.assign(item, updates);
      }),

    navigateToRoom: (roomId) =>
      set((state) => {
        state.assistant.currentRoomId = roomId;
      }),
  }))
);
```

#### Chat Store with WebSocket
```typescript
// stores/chatStore.ts
interface ChatState {
  messages: ChatMessage[];
  isConnected: boolean;
  isTyping: boolean;
  currentModel: string;
  currentProvider: string;

  // WebSocket management
  connect: () => void;
  disconnect: () => void;
  sendMessage: (content: string) => void;
  sendAssistantMove: (x: number, y: number) => void;

  // Message management
  addMessage: (message: ChatMessage) => void;
  clearChat: (clearType: 'current' | 'all' | 'persona', personaName?: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isConnected: false,
  isTyping: false,
  currentModel: 'llama3.2:latest',
  currentProvider: 'ollama',

  connect: () => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      set({ isConnected: true });
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'chat_response':
          get().addMessage({
            id: Date.now().toString(),
            content: data.content,
            sender: 'assistant',
            timestamp: data.timestamp
          });

          // Handle actions if present
          if (data.actions && data.actions.length > 0) {
            // Broadcast actions to room store
            useRoomStore.getState().handleActions(data.actions);
          }
          break;

        case 'typing':
          set({ isTyping: data.isTyping });
          break;

        case 'assistant_update':
          // Update assistant state in room store
          useRoomStore.getState().updateAssistant(data.state);
          break;
      }
    };

    ws.onclose = () => {
      set({ isConnected: false });
      console.log('WebSocket disconnected');

      // Attempt reconnection
      setTimeout(() => get().connect(), 5000);
    };

    // Store reference for sending messages
    (get() as any).ws = ws;
  },

  sendMessage: (content) => {
    const ws = (get() as any).ws;
    if (ws && ws.readyState === WebSocket.OPEN) {
      // Add user message to chat
      get().addMessage({
        id: Date.now().toString(),
        content,
        sender: 'user',
        timestamp: new Date().toISOString()
      });

      // Send to server
      ws.send(JSON.stringify({
        type: 'chat',
        content,
        persona_name: usePersonaStore.getState().selectedPersona?.name
      }));
    }
  },

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message]
    })),
}));
```

### Component Development

#### TopDownRenderer (SVG Floor Plan)
```typescript
// components/FloorPlan/TopDownRenderer.tsx
const TopDownRenderer: React.FC<TopDownRendererProps> = ({
  floorPlan,
  assistant,
  furniture,
  onFurnitureClick,
  onPositionClick,
  deviceType
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewBox, setViewBox] = useState('0 0 1200 800');

  // Calculate viewBox based on floor plan dimensions
  useEffect(() => {
    if (floorPlan) {
      const { width, height } = floorPlan.dimensions;
      setViewBox(`0 0 ${width} ${height}`);
    }
  }, [floorPlan]);

  const handleSvgClick = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * floorPlan.dimensions.width;
    const y = ((e.clientY - rect.top) / rect.height) * floorPlan.dimensions.height;
    onPositionClick?.({ x, y });
  }, [floorPlan, onPositionClick]);

  return (
    <div ref={containerRef} className="floor-plan-container w-full h-full">
      <svg
        viewBox={viewBox}
        className="w-full h-full"
        onClick={handleSvgClick}
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Render rooms */}
        {floorPlan.rooms.map(room => (
          <RoomShape key={room.id} room={room} />
        ))}

        {/* Render walls */}
        {floorPlan.walls.map(wall => (
          <WallLine key={wall.id} wall={wall} />
        ))}

        {/* Render doorways */}
        {floorPlan.doorways.map(doorway => (
          <DoorwayIndicator key={doorway.id} doorway={doorway} />
        ))}

        {/* Render furniture */}
        {furniture.map(item => (
          <FurnitureItem
            key={item.id}
            furniture={item}
            onClick={() => onFurnitureClick?.(item)}
          />
        ))}

        {/* Render assistant */}
        <AssistantSprite
          position={assistant.position}
          facing={assistant.facing}
          mood={assistant.mood}
          isMoving={assistant.isMoving}
        />
      </svg>
    </div>
  );
};
```

### WebSocket Hook
```typescript
// hooks/useWebSocket.ts
export const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setIsConnected(true);
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setSocket(null);

      // Auto-reconnect after 5 seconds
      setTimeout(connect, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }, [socket]);

  useEffect(() => {
    const ws = connect();
    return () => ws?.close();
  }, [connect]);

  return {
    socket,
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect: () => socket?.close()
  };
};
```

## Brain Council System

### Council Architecture

The Brain Council is DeskMate's core AI reasoning system, implementing a multi-perspective approach to decision-making:

```python
class BrainCouncil:
    """
    Multi-perspective AI reasoning system.

    Five council members collaborate to process user requests:
    1. Personality Core - Character consistency
    2. Memory Keeper - Context and history
    3. Spatial Reasoner - Environment understanding
    4. Action Planner - Behavior suggestions
    5. Validator - Safety and feasibility
    """

    async def _run_council_session(self, context: Dict) -> Dict:
        """Run a complete council deliberation session."""

        # Prepare council prompt with structured roles
        council_prompt = self._build_council_prompt(context)

        # Get council reasoning from LLM
        council_response = await llm_manager.chat_completion(
            messages=[{"role": "system", "content": council_prompt}],
            model="gpt-4"  # Use best model for reasoning
        )

        # Parse structured JSON response
        try:
            result = json.loads(council_response)
            return self._validate_council_output(result)
        except json.JSONDecodeError:
            return self._generate_fallback_response(context)

    def _build_council_prompt(self, context: Dict) -> str:
        """Build structured prompt for council deliberation."""

        return f"""
You are the Brain Council for {context['persona_context']['name']},
a virtual AI assistant. Process this request through five perspectives:

## Context
- User Message: {context['user_message']}
- Assistant Position: {context['assistant_state']['position']}
- Room Objects: {context['room_state']['objects']}
- Recent Memories: {context['memories']}

## Council Members

### 1. Personality Core
Analyze how {context['persona_context']['name']} should feel and respond:
- Emotional state based on personality: {context['persona_context']['personality']}
- Appropriate tone and manner of speech
- Character consistency with previous interactions

### 2. Memory Keeper
Consider relevant context:
- Retrieved memories: {context['memories']}
- How past interactions inform current response
- Important context to remember for future

### 3. Spatial Reasoner
Understand the environment:
- Current position and what's visible
- Object locations and accessibility
- Physical constraints and possibilities

### 4. Action Planner
Suggest appropriate actions:
- Movement possibilities
- Object interactions
- Multi-step sequences if needed
- Alternative approaches

### 5. Validator
Ensure feasibility:
- Physical possibility of proposed actions
- Character consistency check
- Safety and appropriateness
- Select best action with confidence rating

## Required Output Format (JSON):
{{
  "personality_core": {{
    "mood": "emotional_state",
    "emotional_reasoning": "why they feel this way",
    "tone": "communication_style"
  }},
  "memory_keeper": {{
    "relevant_memories": ["memory summaries"],
    "context_summary": "how memories inform response"
  }},
  "spatial_reasoner": {{
    "visible_objects": ["objects assistant can see"],
    "reachable_objects": ["objects within interaction range"],
    "spatial_constraints": "movement limitations"
  }},
  "action_planner": {{
    "proposed_actions": [
      {{"type": "action_type", "target": "target", "reasoning": "why"}}
    ]
  }},
  "validator": {{
    "selected_actions": [validated actions],
    "confidence": 0.0-1.0,
    "reasoning": "validation logic"
  }},
  "response_message": "character's response to user"
}}
"""

    def _validate_council_output(self, response: Dict) -> Dict:
        """Validate and sanitize council response."""

        required_sections = [
            "personality_core", "memory_keeper", "spatial_reasoner",
            "action_planner", "validator", "response_message"
        ]

        # Ensure all sections present
        for section in required_sections:
            if section not in response:
                logger.warning(f"Missing council section: {section}")
                response[section] = self._get_default_section(section)

        # Validate actions
        validated_actions = []
        for action in response["validator"].get("selected_actions", []):
            if self._is_valid_action(action):
                validated_actions.append(action)

        response["validator"]["selected_actions"] = validated_actions
        return response

    def _is_valid_action(self, action: Dict) -> bool:
        """Validate individual action structure."""

        required_fields = ["type", "target"]
        valid_types = ["move", "interact", "state_change"]

        return (
            all(field in action for field in required_fields) and
            action["type"] in valid_types and
            self._validate_action_target(action)
        )
```

### Council Member Specializations

#### 1. Personality Core
```python
class PersonalityCore:
    """Maintains character consistency and emotional responses."""

    def analyze_emotional_response(self, context: Dict) -> Dict:
        """Determine appropriate emotional state and response tone."""

        persona = context['persona_context']
        user_message = context['user_message']

        # Analyze message sentiment
        sentiment = self._analyze_sentiment(user_message)

        # Apply personality filter
        base_mood = self._get_base_mood(persona['personality'])
        contextual_mood = self._apply_context(base_mood, sentiment, context)

        return {
            "mood": contextual_mood,
            "emotional_reasoning": f"Based on {persona['name']}'s {persona['personality']} personality and user's {sentiment} message",
            "tone": self._determine_tone(contextual_mood, persona)
        }
```

#### 2. Memory Keeper
```python
class MemoryKeeper:
    """Manages context retrieval and conversation history."""

    async def gather_relevant_context(self, user_message: str, persona_name: str) -> Dict:
        """Retrieve and rank relevant memories."""

        # Search vector database for relevant memories
        memories = await conversation_memory.search_relevant_memories(
            query=user_message,
            persona_name=persona_name,
            limit=10
        )

        # Rank by relevance and recency
        ranked_memories = self._rank_memories(memories, user_message)

        # Summarize context
        context_summary = self._summarize_context(ranked_memories)

        return {
            "relevant_memories": ranked_memories[:5],  # Top 5
            "context_summary": context_summary,
            "memory_confidence": self._calculate_confidence(ranked_memories)
        }
```

#### 3. Spatial Reasoner
```python
class SpatialReasoner:
    """Understands room layout and object relationships."""

    def analyze_spatial_context(self, assistant_state: Dict, room_state: Dict) -> Dict:
        """Analyze spatial relationships and movement possibilities."""

        assistant_pos = assistant_state['position']
        objects = room_state['objects']

        # Calculate visibility
        visible_objects = self._calculate_visible_objects(assistant_pos, objects)

        # Determine reachable objects (within interaction distance)
        reachable_objects = self._find_reachable_objects(assistant_pos, visible_objects)

        # Analyze spatial constraints
        constraints = self._analyze_movement_constraints(assistant_pos, objects)

        return {
            "visible_objects": [obj['name'] for obj in visible_objects],
            "reachable_objects": [obj['name'] for obj in reachable_objects],
            "spatial_constraints": constraints,
            "current_observations": self._generate_observations(visible_objects)
        }

    def _calculate_visible_objects(self, position: Dict, objects: List[Dict]) -> List[Dict]:
        """Calculate which objects are visible from current position."""

        visible = []
        for obj in objects:
            distance = self._calculate_distance(position, obj['position'])

            # Objects within 10 cells are clearly visible
            if distance <= 10:
                visible.append({**obj, "visibility": "clear", "distance": distance})
            # Objects within 20 cells are partially visible
            elif distance <= 20:
                visible.append({**obj, "visibility": "partial", "distance": distance})

        return sorted(visible, key=lambda x: x['distance'])
```

#### 4. Action Planner
```python
class ActionPlanner:
    """Generates and evaluates possible actions."""

    def propose_actions(self, context: Dict) -> List[Dict]:
        """Generate action proposals based on context."""

        user_intent = self._analyze_user_intent(context['user_message'])
        spatial_context = context['spatial_analysis']
        assistant_state = context['assistant_state']

        proposals = []

        # Movement actions
        if user_intent.get('movement_requested'):
            movement_actions = self._plan_movement_actions(user_intent, spatial_context)
            proposals.extend(movement_actions)

        # Interaction actions
        if user_intent.get('interaction_requested'):
            interaction_actions = self._plan_interaction_actions(user_intent, spatial_context)
            proposals.extend(interaction_actions)

        # State change actions
        if user_intent.get('state_change_requested'):
            state_actions = self._plan_state_changes(user_intent, assistant_state)
            proposals.extend(state_actions)

        # Conversational actions (always available)
        proposals.extend(self._plan_conversational_actions(context))

        return self._rank_action_proposals(proposals, context)
```

#### 5. Validator
```python
class Validator:
    """Ensures action feasibility and safety."""

    def validate_action_sequence(self, proposed_actions: List[Dict], context: Dict) -> Dict:
        """Validate and select optimal action sequence."""

        valid_actions = []
        confidence_scores = []

        for action in proposed_actions:
            validation_result = self._validate_single_action(action, context)

            if validation_result['is_valid']:
                valid_actions.append(action)
                confidence_scores.append(validation_result['confidence'])

        # Select best actions based on validation
        selected_actions = self._select_optimal_actions(valid_actions, confidence_scores)

        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0

        return {
            "selected_actions": selected_actions,
            "confidence": overall_confidence,
            "validation_reasoning": self._explain_validation(selected_actions),
            "rejected_actions": [a for a in proposed_actions if a not in valid_actions]
        }

    def _validate_single_action(self, action: Dict, context: Dict) -> Dict:
        """Validate a single action for feasibility."""

        action_type = action.get('type')

        if action_type == 'move':
            return self._validate_movement(action, context)
        elif action_type == 'interact':
            return self._validate_interaction(action, context)
        elif action_type == 'state_change':
            return self._validate_state_change(action, context)

        return {"is_valid": False, "confidence": 0.0, "reason": "Unknown action type"}

    def _validate_movement(self, action: Dict, context: Dict) -> Dict:
        """Validate movement action."""

        target = action.get('target', {})
        assistant_pos = context['assistant_state']['position']
        room_bounds = context['room_state']['grid_size']

        # Check bounds
        if not (0 <= target.get('x', -1) < room_bounds['width'] and
                0 <= target.get('y', -1) < room_bounds['height']):
            return {"is_valid": False, "confidence": 0.0, "reason": "Target outside room bounds"}

        # Check path feasibility (simplified)
        distance = abs(target['x'] - assistant_pos['x']) + abs(target['y'] - assistant_pos['y'])

        if distance > 30:  # Reasonable movement distance
            return {"is_valid": False, "confidence": 0.0, "reason": "Movement distance too large"}

        return {"is_valid": True, "confidence": 0.9, "reason": "Valid movement target"}
```

## API Reference

### Authentication
Currently, DeskMate does not require authentication for local development. In production, consider implementing:
- API key authentication for external access
- JWT tokens for session management
- Rate limiting for abuse prevention

### Core Endpoints

#### Health and Status
```http
GET /health
```
Returns system health status.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2023-01-01T12:00:00Z",
  "services": {
    "database": "connected",
    "vector_db": "connected",
    "llm_providers": ["ollama", "nano_gpt"]
  }
}
```

#### Brain Council API

##### Process Message
```http
POST /brain/process
Content-Type: application/json

{
  "message": "Turn on the lamp and move to the bed",
  "persona_context": {
    "name": "Alice",
    "personality": "Friendly and helpful",
    "current_mood": "cheerful"
  }
}
```

**Response:**
```json
{
  "response": "I'll turn on the lamp and then move to the bed for you!",
  "actions": [
    {
      "type": "move",
      "target": {"x": 15, "y": 5},
      "parameters": {"reason": "Moving to lamp"}
    },
    {
      "type": "interact",
      "target": "lamp_001",
      "parameters": {"action": "turn_on"}
    },
    {
      "type": "move",
      "target": {"x": 7, "y": 11},
      "parameters": {"reason": "Moving to bed"}
    }
  ],
  "mood": "helpful",
  "confidence": 0.92,
  "processing_time": 1.24
}
```

##### Analyze Context
```http
POST /brain/analyze
Content-Type: application/json

{
  "include_memory": true,
  "persona_name": "Alice"
}
```

#### Assistant API

##### Get Assistant State
```http
GET /assistant
```

**Response:**
```json
{
  "position": {"x": 32, "y": 8},
  "facing": "right",
  "current_action": "idle",
  "mood": "neutral",
  "expression": "neutral.png",
  "energy": 0.8,
  "status": "active",
  "holding_object_id": null,
  "sitting_on_object_id": null
}
```

##### Move Assistant
```http
POST /assistant/move
Content-Type: application/json

{
  "x": 20,
  "y": 10
}
```

#### Chat API

##### Simple Chat
```http
POST /chat/simple
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "persona_name": "Alice"
}
```

##### Get Available Models
```http
GET /chat/models
```

**Response:**
```json
{
  "ollama": ["llama3.2:latest", "phi3:mini", "gemma-2b"],
  "nano_gpt": ["gpt-4", "gpt-3.5-turbo"]
}
```

#### Memory API

##### Memory Statistics
```http
GET /conversation/memory/stats
```

##### Clear Memory
```http
POST /conversation/memory/clear
POST /conversation/memory/clear-all
POST /conversation/memory/clear-persona?persona_name=Alice
```

### WebSocket API

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

#### Message Types

##### Chat Message
```json
{
  "type": "chat",
  "content": "Hello, how are you?",
  "persona_name": "Alice"
}
```

##### Assistant Movement
```json
{
  "type": "assistant_move",
  "x": 20,
  "y": 10
}
```

##### Status Request
```json
{
  "type": "status_request"
}
```

#### Response Types

##### Chat Response
```json
{
  "type": "chat_response",
  "content": "I'm doing well, thank you!",
  "actions": [...],
  "mood": "happy",
  "timestamp": "2023-01-01T12:00:00Z"
}
```

##### Typing Indicator
```json
{
  "type": "typing",
  "isTyping": true
}
```

##### Assistant Update
```json
{
  "type": "assistant_update",
  "state": {
    "position": {"x": 20, "y": 10},
    "mood": "happy",
    "current_action": "walking"
  }
}
```

## Database Design

### PostgreSQL Schema

#### Assistants Table
```sql
CREATE TABLE assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_x INTEGER NOT NULL DEFAULT 32,
    position_y INTEGER NOT NULL DEFAULT 8,
    facing VARCHAR(10) NOT NULL DEFAULT 'right',
    current_action VARCHAR(50) DEFAULT 'idle',
    mood VARCHAR(20) DEFAULT 'neutral',
    expression VARCHAR(100) DEFAULT 'neutral.png',
    energy DECIMAL(3,2) DEFAULT 1.0,
    status VARCHAR(20) DEFAULT 'active',
    holding_object_id UUID,
    sitting_on_object_id UUID,
    last_action_time TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Room Objects Table
```sql
CREATE TABLE room_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    object_type VARCHAR(50) NOT NULL,
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    size_width INTEGER NOT NULL DEFAULT 1,
    size_height INTEGER NOT NULL DEFAULT 1,
    sprite_path VARCHAR(200),
    is_movable BOOLEAN DEFAULT false,
    is_interactive BOOLEAN DEFAULT true,
    is_walkable BOOLEAN DEFAULT false,
    current_state JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Object States Table
```sql
CREATE TABLE object_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id UUID NOT NULL REFERENCES room_objects(id),
    state_key VARCHAR(50) NOT NULL,
    state_value VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(object_id, state_key)
);
```

### Qdrant Collections

#### Conversation Memory Collection
```python
collection_config = {
    "vectors": {
        "size": 384,  # Sentence transformer dimension
        "distance": "Cosine"
    }
}

# Point structure
{
    "id": "unique_memory_id",
    "vector": [0.1, 0.2, ...],  # 384-dimensional embedding
    "payload": {
        "content": "User asked about turning on the lamp",
        "persona_name": "Alice",
        "memory_type": "conversation",
        "timestamp": "2023-01-01T12:00:00Z",
        "metadata": {
            "user_emotion": "neutral",
            "assistant_action": "lamp_interaction",
            "objects_involved": ["lamp_001"]
        }
    }
}
```

#### Dreams Collection (Idle Mode)
```python
# Separate collection for autonomous behavior memories
{
    "id": "dream_id",
    "vector": [0.1, 0.2, ...],
    "payload": {
        "content": "Moved to window and looked outside",
        "persona_name": "Alice",
        "memory_type": "dream",
        "timestamp": "2023-01-01T12:00:00Z",
        "expires_at": "2023-01-02T12:00:00Z",  # 24 hour expiration
        "metadata": {
            "autonomous_action": true,
            "energy_level": 0.6,
            "mood": "curious"
        }
    }
}
```

## Testing Framework

### Test Structure

```
tests/
├── backend/
│   ├── unit/
│   │   ├── test_brain_council.py
│   │   ├── test_action_executor.py
│   │   ├── test_conversation_memory.py
│   │   └── test_pathfinding.py
│   ├── integration/
│   │   ├── test_websocket_integration.py
│   │   ├── test_api_integration.py
│   │   └── test_database_integration.py
│   └── e2e/
│       └── test_full_workflows.py
├── frontend/
│   ├── unit/
│   │   ├── components/
│   │   ├── stores/
│   │   └── hooks/
│   ├── integration/
│   └── e2e/
└── load-testing/
    ├── locustfile.py
    └── performance_tests.py
```

### Running Tests

#### Backend Tests
```bash
# Unit tests
pytest backend/tests/unit/ -v

# Integration tests
pytest backend/tests/integration/ -v

# With coverage
pytest --cov=app --cov-report=html backend/tests/

# Specific test
pytest backend/tests/unit/test_brain_council.py::TestBrainCouncilBasic::test_process_simple_message -v
```

#### Frontend Tests
```bash
# Unit tests
npm test

# With coverage
npm run test:coverage

# E2E tests
npm run test:e2e

# Specific component
npm test -- --testNamePattern="Grid Component"
```

#### Load Testing
```bash
# Quick load test
cd load-testing
./run_load_tests.sh basic

# Stress test
./run_load_tests.sh stress

# Interactive testing
./run_load_tests.sh interactive
```

### Test Data Management

#### Test Fixtures
```python
# backend/tests/conftest.py
@pytest.fixture
def mock_brain_council_response():
    return {
        "response": "I'll help you with that!",
        "actions": [
            {
                "type": "move",
                "target": {"x": 20, "y": 10},
                "parameters": {"reason": "Moving to requested position"}
            }
        ],
        "mood": "helpful",
        "confidence": 0.9
    }

@pytest.fixture
def test_room_state():
    return {
        "objects": [
            {
                "id": "lamp_001",
                "name": "Desk Lamp",
                "position": {"x": 15, "y": 5},
                "type": "item",
                "interactive": True
            }
        ],
        "grid_size": {"width": 64, "height": 16}
    }
```

#### Database Test Setup
```python
# backend/tests/conftest.py
@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    test_db_url = "postgresql://test:test@localhost:5433/test_deskmate"

    engine = create_engine(test_db_url)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """Create test database session."""
    connection = test_db.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

## Deployment

### Development Deployment
```bash
# Quick start
docker-compose up -d

# Development mode with hot reload
docker-compose -f docker-compose.dev.yml up -d
```

### Production Deployment

#### Docker Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

#### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deskmate-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deskmate-backend
  template:
    metadata:
      labels:
        app: deskmate-backend
    spec:
      containers:
      - name: backend
        image: deskmate/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: deskmate-secrets
              key: database-url
        - name: NANO_GPT_API_KEY
          valueFrom:
            secretKeyRef:
              name: deskmate-secrets
              key: nano-gpt-key
```

#### Environment Configuration
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/deskmate
QDRANT_URL=http://qdrant:6333

# LLM Configuration
NANO_GPT_API_KEY=your_production_key
OLLAMA_BASE_URL=http://ollama:11434

# Security
CORS_ORIGINS=["https://yourdomain.com"]
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Performance
LLM_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=10
```

## Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YourBr0ther/deskmate.git
   cd deskmate
   git remote add upstream https://github.com/YourBr0ther/deskmate.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Development Setup**
   ```bash
   # Install dependencies
   cd backend && pip install -r requirements.txt
   cd ../frontend && npm install

   # Start development environment
   docker-compose up -d deskmate-postgres deskmate-qdrant
   ```

4. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation
   - Ensure all tests pass

5. **Testing**
   ```bash
   # Backend tests
   cd backend && pytest -v

   # Frontend tests
   cd frontend && npm test

   # E2E tests
   npm run test:e2e
   ```

6. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Describe changes and motivation
   - Reference related issues
   - Ensure CI passes

### Code Style Guidelines

#### Python (Backend)
```python
# Use ruff for formatting and linting
ruff format .
ruff check .

# Type hints required
def process_message(message: str, persona: Optional[Dict]) -> Dict[str, Any]:
    """Process message with type safety."""
    pass

# Docstrings for classes and public methods
class BrainCouncil:
    """Multi-perspective AI reasoning system.

    Coordinates five AI specialists to process user requests
    and generate contextually appropriate responses.
    """

    async def process_user_message(self, message: str) -> Dict:
        """Process user message through council deliberation.

        Args:
            message: User's input message

        Returns:
            Dict containing response, actions, and metadata
        """
```

#### TypeScript (Frontend)
```typescript
// Use Prettier and ESLint
npm run lint
npm run format

// Strict typing
interface BrainCouncilResponse {
  response: string;
  actions: Action[];
  mood: MoodType;
  confidence: number;
}

// Props interfaces for components
interface GridProps {
  gridSize: { width: number; height: number };
  cellSize: { width: number; height: number };
  onCellClick: (position: Position) => void;
}

// Prefer functional components with hooks
const Grid: React.FC<GridProps> = ({ gridSize, cellSize, onCellClick }) => {
  // Component implementation
};
```

### Architecture Decisions

When contributing, consider these architectural principles:

1. **Separation of Concerns**
   - Brain Council handles AI reasoning
   - Action Executor handles implementation
   - Services handle business logic
   - API layer handles communication

2. **State Management**
   - Zustand for client state
   - PostgreSQL for persistent data
   - Qdrant for vector data
   - WebSocket for real-time updates

3. **Error Handling**
   - Graceful degradation
   - User-friendly error messages
   - Comprehensive logging
   - Fallback mechanisms

4. **Performance**
   - Async/await throughout
   - Database connection pooling
   - Vector search optimization
   - WebSocket for real-time features

### Documentation Requirements

- Update API documentation for new endpoints
- Add inline comments for complex logic
- Update user guides for new features
- Include example usage in docstrings
- Update architecture diagrams if needed

---

*For user-facing documentation, see the [User Guide](USER_GUIDE.md) and [Setup Guide](SETUP_GUIDE.md).*