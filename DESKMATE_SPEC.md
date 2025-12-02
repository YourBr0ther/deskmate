# DeskMate - Virtual AI Companion Specification

## Project Overview

DeskMate is a virtual AI companion that lives in a simulated room environment displayed on a secondary 1920x480 monitor. The companion uses LLM technology and persona cards (SillyTavern-compatible) to create an interactive, living desktop assistant that can move around their environment, interact with objects, and engage in conversations.

## Display Layout (1920x480)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Grid View (1280x480)           │  Companion Panel (640x480)            │
│  ┌──────────────────────────┐   │  ┌────────────────────────────────┐  │
│  │                          │   │  │  [Portrait 400x400]            │  │
│  │   Room Environment       │   │  │                                │  │
│  │   (64x16 grid)           │   │  │  Character Name                │  │
│  │   30px per cell          │   │  │  ────────────────              │  │
│  │                          │   │  │  Status: [Active/Idle/Busy]    │  │
│  │                          │   │  │  Mood: [Happy/Neutral/Sad]     │  │
│  │                          │   │  │  Activity: [Current Action]    │  │
│  └──────────────────────────┘   │  │                                │  │
│                                   │  │  ────────────────              │  │
│                                   │  │  [Time/Date Display]           │  │
│                                   │  └────────────────────────────────┘  │
│                                   │                                      │
│                                   │  [Chat Window - 640x80]              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **LLM Orchestration**: LangChain
- **Vector Database**: Qdrant (for memory storage)
- **LLM Providers**: 
  - Nano-GPT API (https://nano-gpt.com/api)
  - Ollama (local models)
- **Pathfinding**: A* algorithm implementation
- **Image Processing**: Pillow (for PNG persona card extraction)

### Frontend
- **Framework**: React 18+ with TypeScript
- **Deployment**: Web-based (responsive design)
- **State Management**: Zustand
- **Styling**: TailwindCSS
- **Grid Rendering**: HTML5 Canvas or React-Grid-Layout
- **Drag-and-Drop**: react-dnd

### Infrastructure
- **Containerization**: Docker Compose
- **Storage**: PostgreSQL (metadata), Qdrant (vectors)
- **File Storage**: Local filesystem (persona cards, objects)

### GitHub
- **Repository**: github.com/yourbr0ther/DeskMate
- **Structure**: Monorepo

## Core Features

### 1. Persona System (SillyTavern Compatible)
- Load PNG files with embedded JSON metadata (V2 spec)
- Extract character information: name, description, personality, example dialogues
- Support for expression images (happy, sad, angry, etc.)
- Fallback to default PNG if expressions not available

### 2. Room Environment
- **Grid System**: 64 columns × 16 rows (1920x480 @ 30px per cell)
- **Object Types**:
  - **Large Objects** (hardcoded, immovable): bed, desk, window, door, bookshelf
  - **Small Objects** (movable): lamp, book, mug, plant, picture frame
  - **Storage Closet**: Virtual inventory for items not in room
- **Object Properties**:
  - Position (x, y)
  - Size (width, height in cells)
  - Pixel identifier (simple sprite/icon)
  - Description (for LLM context)
  - State string (open/closed, on/off, color variants)
  - Interactable flag
  - Walkable flag (can assistant walk through it?)

### 3. Virtual Assistant Behavior

#### Active Mode (User Present)
- Responds to chat messages in real-time
- Uses primary LLM (Nano-GPT API or Ollama with larger models)
- Moves around room based on conversation context
- Interacts with objects when relevant
- Updates portrait based on mood/expression

#### Idle Mode (After 10 Minutes Inactivity)
- Automatically triggered after 10 minutes of no user input
- Manually triggered with `/idle` command
- Switches to lightweight Ollama models (phi-3, gemma-2b, llama3.2-1b)
- Performs autonomous actions slower (1 action per 2-5 minutes)
- Actions stored as "dreams" in separate Qdrant collection
- Dreams fade after 24 hours
- Can reference dreams when returning to active mode

### 4. Brain Council System

Five-member council using single LLM with structured reasoning:

**1. Personality Core**
- Maintains character consistency
- Generates dialogue in character's voice
- Manages emotional states
- Ensures responses match persona card

**2. Memory Keeper**
- Queries Qdrant for relevant past conversations
- Retrieves context about objects, previous actions
- Manages working memory (recent actions)
- Filters dreams vs real memories

**3. Spatial Reasoner**
- Understands room layout
- Knows object positions and states
- Calculates pathfinding
- Determines what's visible from current position

**4. Action Planner**
- Decides next action based on:
  - Current conversation
  - Character personality
  - Room state
  - Recent actions
  - Needs/goals
- Generates action proposals

**5. Validator**
- Checks if proposed actions make sense
- Validates consistency with character
- Ensures physical plausibility
- Prevents contradictions

**Council Process**:
1. Gather inputs (chat, position, recent actions, room state)
2. Each member provides structured reasoning
3. Combine insights into single decision
4. Execute action with confidence score

### 5. Chat System

**Commands**:
- `/idle` - Force idle mode
- `/create [description]` - Create new object in storage closet
- Standard chat - Talk with assistant

**Chat Modes**:
- User ↔ Assistant conversation
- User → Room commands ("move the lamp to the desk")
- Assistant can respond to both naturally

**Storage**:
- All conversations stored in Qdrant (long-term memory)
- Idle/dream conversations stored separately
- Embeddings for semantic search
- Metadata: timestamp, mode (active/idle), participants

### 6. Object Creation System

User can create objects via `/create` command:

```
User: /create a red coffee mug with a heart on it
System: [LLM generates]
- Name: "Heart Coffee Mug"
- Description: "A red ceramic mug with a white heart design"
- Pixel sprite: [simple 2-3 color icon]
- Initial state: "empty"
- Size: 1x1 cells
- Properties: movable, fillable
→ Placed in storage closet
```

### 7. Interaction System

**User Interactions**:
- Click and drag objects between grid cells
- Chat commands to assistant
- Click assistant to get attention
- Click objects to inspect

**Assistant Interactions**:
- Walk to objects (A* pathfinding)
- Pick up/put down small objects
- Sit on furniture
- Open/close doors, drawers
- Turn on/off lights
- Look out window
- Read books
- All actions narrated in chat

## Data Models

### Persona Card (V2 Spec)
```json
{
  "spec": "chara_card_v2",
  "spec_version": "2.0",
  "data": {
    "name": "Character Name",
    "description": "Physical description",
    "personality": "Personality traits",
    "scenario": "Current situation",
    "first_mes": "First message",
    "mes_example": "Example dialogues",
    "creator_notes": "Notes from creator",
    "system_prompt": "System instructions",
    "post_history_instructions": "Instructions after history",
    "alternate_greetings": ["Alt greeting 1", "Alt greeting 2"],
    "character_book": { /* lore book */ },
    "tags": ["tag1", "tag2"],
    "creator": "Creator name",
    "character_version": "1.0",
    "extensions": {
      "expressions": {
        "happy": "happy.png",
        "sad": "sad.png",
        "angry": "angry.png",
        "neutral": "neutral.png"
      }
    }
  }
}
```

### Room Object
```python
{
  "id": "uuid",
  "name": "Object Name",
  "description": "Detailed description for LLM",
  "position": {"x": 10, "y": 5},
  "size": {"width": 2, "height": 1},
  "sprite": "lamp_icon.png",
  "state": "on",
  "properties": {
    "movable": True,
    "walkable": False,
    "interactable": True,
    "sittable": False
  },
  "created_at": "timestamp",
  "created_by": "user|assistant|system"
}
```

### Memory Entry
```python
{
  "id": "uuid",
  "type": "conversation|action|dream",
  "content": "Text content",
  "embedding": [0.1, 0.2, ...],
  "metadata": {
    "timestamp": "ISO8601",
    "mode": "active|idle",
    "participants": ["user", "assistant"],
    "room_state_snapshot": {},
    "assistant_position": {"x": 10, "y": 5}
  },
  "expires_at": "timestamp"  # Only for dreams
}
```

### Assistant State
```python
{
  "position": {"x": 32, "y": 8},
  "facing": "left|right|up|down",
  "current_action": "walking|sitting|talking|idle",
  "mood": "happy|neutral|sad|angry|surprised",
  "expression": "happy.png",
  "holding_object": "object_id|null",
  "last_action_time": "timestamp",
  "mode": "active|idle",
  "energy": 0.8,  # For future needs system
  "goals": ["current goals"],
  "working_memory": ["recent actions"]
}
```

## Development Phases

### Phase 1: Foundation & Infrastructure (Week 1-2)
**Goal**: Set up project structure, Docker environment, basic backend

**Deliverables**:
- Project repository structure
- Docker Compose configuration
  - FastAPI backend container
  - Qdrant container
  - PostgreSQL container
- Basic FastAPI app with health check
- Qdrant connection and basic operations
- Environment variable management
- Basic logging setup

**Acceptance Criteria**:
- `docker-compose up` starts all services
- API accessible at localhost:8000
- Qdrant accessible and queryable
- Basic health check endpoint returns 200

### Phase 2: Persona System & Basic Frontend (Week 3-4)
**Goal**: Load persona cards, render basic UI

**Deliverables**:
- PNG persona card reader (extract embedded JSON)
- Persona validation and parsing
- React web app with responsive design
- Display persona portrait and name
- Basic grid rendering (responsive 64x16 on desktop, 8x8 on mobile)
- Expression system (with fallback to default)

**Acceptance Criteria**:
- Can load SillyTavern V2 persona cards
- Portrait displays correctly (responsive sizing)
- Grid renders responsively (desktop: left 2/3, mobile: stacked)
- Can switch between expressions
- Web app accessible via browser with mobile support

### Phase 3: Room Environment & Objects (Week 5-6)
**Goal**: Create interactive room with objects

**Deliverables**:
- Hardcoded large objects (bed, desk, window, door)
- Small object system
- Storage closet functionality
- Object rendering on grid (simple sprites)
- Click and drag for small objects
- Object state management
- PostgreSQL schemas for objects

**Acceptance Criteria**:
- Room loads with preset furniture
- Objects render at correct grid positions
- Can drag small objects between cells
- Objects have collision detection
- Storage closet shows hidden objects
- Object states persist in database

### Phase 4: Assistant Movement & Pathfinding (Week 7-8)
**Goal**: Assistant can navigate room

**Deliverables**:
- A* pathfinding algorithm
- Assistant sprite/representation on grid
- Walking animation (grid-hop)
- Collision detection (can't walk through large objects)
- Walk-through for small objects
- Sitting on furniture
- Position tracking in database

**Acceptance Criteria**:
- Assistant can pathfind to any reachable cell
- Walks around furniture
- Can sit on bed/chair
- Movement is smooth and logical
- Position persists between sessions

### Phase 5: LLM Integration (Week 9-10)
**Goal**: Connect to LLM providers

**Deliverables**:
- Nano-GPT API integration
- Ollama integration
- Model selection UI
- Basic prompt engineering
- Response streaming
- Error handling and retries
- Token usage tracking

**Acceptance Criteria**:
- Can select between Nano-GPT and Ollama
- Can choose specific models
- LLM responds to basic prompts
- Responses stream to UI
- Graceful handling of API failures

### Phase 6: Chat System & Memory (Week 11-12)
**Goal**: Functional chat with memory

**Deliverables**:
- Chat UI component
- Message history display
- Vector embedding generation
- Qdrant memory storage
- Memory retrieval (semantic search)
- Conversation context management
- `/create` command implementation
- Basic object generation with LLM

**Acceptance Criteria**:
- Can chat with assistant
- Messages display in UI
- Conversation persists in Qdrant
- Assistant remembers past conversations
- `/create` generates objects with descriptions and sprites
- Created objects appear in storage

### Phase 7: Brain Council System (Week 13-14)
**Goal**: Implement multi-perspective reasoning

**Deliverables**:
- Brain council prompt structure
- Five-member council implementation:
  1. Personality Core
  2. Memory Keeper
  3. Spatial Reasoner
  4. Action Planner
  5. Validator
- Structured reasoning output
- Action decision pipeline
- Council debate logging (for debugging)

**Acceptance Criteria**:
- Each council member provides input
- Combined reasoning produces coherent action
- Actions consistent with character
- Council process completes in <5 seconds
- Debug logs show council reasoning

### Phase 8: Action Execution & Interaction (Week 15-16)
**Goal**: Assistant can perform actions

**Deliverables**:
- Action execution system
- Assistant can move objects
- Assistant can change object states
- Action narration in chat
- Multi-step action sequences
- User command parsing
- Room command handling

**Acceptance Criteria**:
- Assistant responds to "move the lamp to desk"
- Actions narrated naturally in character
- Objects update positions/states correctly
- Assistant's movement syncs with actions
- Failed actions handled gracefully

### Phase 9: Idle Mode & Dreams (Week 17-18)
**Goal**: Autonomous behavior when user away

**Deliverables**:
- Inactivity detection (10 minutes)
- `/idle` command
- Idle mode LLM switching (to Ollama lightweight)
- Autonomous action generation (slower pace)
- Dream storage in separate Qdrant collection
- Dream expiration (24 hours)
- Active mode resume with dream context

**Acceptance Criteria**:
- Idle mode triggers after 10 minutes
- Assistant performs 1 action per 2-5 minutes in idle
- Dreams stored separately from real memories
- Dreams expire after 24 hours
- Assistant can reference dreams when reactivated
- Smooth transition between modes

### Phase 10: Polish & UX Improvements (Week 19-20)
**Goal**: Enhance user experience

**Deliverables**:
- Status indicators (mood, activity, mode)
- Time/date display
- Improved chat UI (message timestamps, typing indicator)
- Expression transitions (smooth mood changes)
- Object inspection (click to see details)
- Assistant attention system (click to interrupt)
- Settings panel (model selection, persona switching)
- Performance optimization

**Acceptance Criteria**:
- UI feels responsive and polished
- All status information clearly visible
- Easy to switch personas and models
- No lag in chat or grid rendering
- Assistant feels "alive" and responsive

### Phase 11: Testing & Documentation (Week 21-22)
**Goal**: Ensure reliability and usability

**Deliverables**:
- Unit tests (backend)
- Integration tests
- End-to-end tests (Playwright)
- Load testing (memory usage, performance)
- User documentation (README, setup guide)
- Developer documentation (architecture, API docs)
- Persona creation guide
- Object creation guide

**Acceptance Criteria**:
- >80% code coverage
- All critical paths tested
- No memory leaks
- Documentation clear and complete
- Easy for new users to set up

### Phase 12: Deployment & Advanced Features (Week 23-24)
**Goal**: Production-ready and extensible

**Deliverables**:
- Production Docker Compose config
- Ubuntu server deployment guide
- Backup/restore system
- Logging and monitoring
- Multiple room templates
- Room customization UI
- Export/import personas
- Export/import room configurations

**Acceptance Criteria**:
- Deploys cleanly to Ubuntu server
- Data backed up regularly
- Logs accessible and useful
- Can switch between room templates
- Easy to share personas and rooms

## Architecture Diagrams

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│  React Web App (Responsive Design)                              │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐│
│  │  Grid Canvas         │  │  Companion Panel                 ││
│  │  (Room Renderer)     │  │  - Portrait                      ││
│  │                      │  │  - Status                        ││
│  └──────────────────────┘  │  - Chat                          ││
│                             └──────────────────────────────────┘│
│                 ▲                          │                     │
│                 │ WebSocket                │ REST API            │
│                 ▼                          ▼                     │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│  FastAPI Backend                                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ WebSocket       │  │ LLM Router   │  │ Brain Council    │ │
│  │ Manager         │  │ - Nano-GPT   │  │ Orchestrator     │ │
│  │                 │  │ - Ollama     │  │                  │ │
│  └─────────────────┘  └──────────────┘  └──────────────────┘ │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Persona Manager │  │ Room Manager │  │ Memory Manager   │ │
│  └─────────────────┘  └──────────────┘  └──────────────────┘ │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Action Executor │  │ Pathfinding  │  │ Idle Controller  │ │
│  └─────────────────┘  └──────────────┘  └──────────────────┘ │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│  Data Layer                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ PostgreSQL   │  │ Qdrant       │  │ File System        │  │
│  │ - Objects    │  │ - Memories   │  │ - Personas         │  │
│  │ - States     │  │ - Dreams     │  │ - Sprites          │  │
│  │ - Metadata   │  │ - Embeddings │  │ - Room Templates   │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Brain Council Flow
```
┌──────────────────────────────────────────────────────────────┐
│  Input Gathering                                             │
│  - Current chat message (if any)                             │
│  - Assistant position & facing                               │
│  - Room state (object positions, states)                     │
│  - Recent actions (last 5)                                   │
│  - Working memory                                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Council Member Deliberation (Parallel)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Personality Core                                  │   │
│  │    "Given character traits, how should they feel     │   │
│  │     and speak about this situation?"                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. Memory Keeper                                     │   │
│  │    "What relevant past conversations or experiences  │   │
│  │     should inform this decision?"                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. Spatial Reasoner                                  │   │
│  │    "Where am I? What can I see? What's reachable?    │   │
│  │     What makes sense physically?"                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. Action Planner                                    │   │
│  │    "What are 3 possible next actions and why?"       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 5. Validator                                         │   │
│  │    "Do these proposals make sense given everything?" │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Synthesis                                                    │
│  - Combine all perspectives                                  │
│  - Resolve conflicts                                         │
│  - Select best action with confidence score                  │
│  - Generate natural language response                        │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  Action Execution                                            │
│  - Move assistant (if needed)                                │
│  - Update object states                                      │
│  - Send chat message                                         │
│  - Store in memory                                           │
└──────────────────────────────────────────────────────────────┘
```

## File Structure

```
DeskMate/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── persona-guide.md
│   └── development.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── persona.py
│   │   │   ├── room.py
│   │   │   ├── object.py
│   │   │   ├── memory.py
│   │   │   └── assistant.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── persona_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── memory_service.py
│   │   │   ├── room_service.py
│   │   │   ├── pathfinding.py
│   │   │   ├── brain_council.py
│   │   │   ├── action_executor.py
│   │   │   └── idle_controller.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── personas.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── room.py
│   │   │   │   ├── objects.py
│   │   │   │   └── assistant.py
│   │   │   └── websocket.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── postgres.py
│   │   │   └── qdrant.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── image.py
│   │       ├── embeddings.py
│   │       └── logging.py
│   └── tests/
│       ├── __init__.py
│       ├── test_persona.py
│       ├── test_pathfinding.py
│       ├── test_brain_council.py
│       └── test_memory.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── electron.js
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── Grid/
│   │   │   │   ├── Grid.tsx
│   │   │   │   ├── GridCell.tsx
│   │   │   │   ├── Assistant.tsx
│   │   │   │   └── RoomObject.tsx
│   │   │   ├── Companion/
│   │   │   │   ├── Portrait.tsx
│   │   │   │   ├── StatusPanel.tsx
│   │   │   │   └── InfoDisplay.tsx
│   │   │   ├── Chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   └── ChatInput.tsx
│   │   │   └── Settings/
│   │   │       ├── SettingsPanel.tsx
│   │   │       ├── PersonaSelector.tsx
│   │   │       └── ModelSelector.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── usePersona.ts
│   │   │   ├── useRoom.ts
│   │   │   └── useAssistant.ts
│   │   ├── stores/
│   │   │   ├── personaStore.ts
│   │   │   ├── roomStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── assistantStore.ts
│   │   ├── utils/
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── pathfinding.ts
│   │   └── types/
│   │       ├── persona.ts
│   │       ├── room.ts
│   │       ├── message.ts
│   │       └── assistant.ts
│   └── tests/
│       └── App.test.tsx
└── data/
    ├── personas/
    │   └── .gitkeep
    ├── sprites/
    │   ├── objects/
    │   └── expressions/
    └── rooms/
        └── default-room.json
```

## Configuration

### Environment Variables (.env)
```bash
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=true

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=deskmate
POSTGRES_USER=deskmate
POSTGRES_PASSWORD=changeme

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=

# LLM Providers
NANO_GPT_API_KEY=your_nano_gpt_api_key
NANO_GPT_BASE_URL=https://nano-gpt.com/api
OLLAMA_HOST=http://host.docker.internal:11434

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Application
DEFAULT_PERSONA=default.png
IDLE_TIMEOUT_MINUTES=10
IDLE_ACTION_INTERVAL_SECONDS=180
DREAM_EXPIRATION_HOURS=24
MAX_WORKING_MEMORY=10
```

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./backend/app:/app/app
    environment:
      - POSTGRES_HOST=postgres
      - QDRANT_HOST=qdrant
    depends_on:
      - postgres
      - qdrant
    networks:
      - deskmate

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=deskmate
      - POSTGRES_USER=deskmate
      - POSTGRES_PASSWORD=changeme
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - deskmate

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - deskmate

volumes:
  postgres_data:
  qdrant_data:

networks:
  deskmate:
    driver: bridge
```

## Key Algorithms

### A* Pathfinding
```python
def a_star_pathfinding(start, goal, grid, assistant_size):
    """
    Find shortest path from start to goal on grid.
    
    Args:
        start: (x, y) tuple
        goal: (x, y) tuple
        grid: 2D array of cell states
        assistant_size: (width, height) in cells
    
    Returns:
        List of (x, y) positions from start to goal
    """
    # Implementation considers:
    # - Large objects block movement
    # - Small objects can be walked through
    # - Assistant occupies multiple cells
    # - Heuristic: Manhattan distance
    pass
```

### Brain Council Prompt Structure
```python
COUNCIL_PROMPT = """
You are the Brain Council for {character_name}, an AI assistant living in a virtual room.

## Current Situation
- Position: {position}
- Facing: {facing}
- Current Action: {current_action}
- Room State: {room_state}
- Recent Actions: {recent_actions}
- User Message: {user_message}

## Character Context
{character_description}
{character_personality}

## Council Members
Each member provides their perspective:

### 1. Personality Core
How should {character_name} feel and respond based on their personality?
Consider emotions, speech patterns, and character consistency.

### 2. Memory Keeper
What relevant memories inform this moment?
Retrieved memories: {retrieved_memories}

### 3. Spatial Reasoner
What does {character_name} perceive in the room right now?
What objects are nearby? What's reachable?

### 4. Action Planner
What are 3 possible actions {character_name} could take next and why?
Consider goals, needs, and context.

### 5. Validator
Do the proposed actions make sense given:
- Character consistency
- Physical constraints
- Current context

## Output Format (JSON)
{{
  "personality_core": {{
    "mood": "happy|neutral|sad|angry|surprised",
    "emotional_reasoning": "why they feel this way",
    "tone": "how they should speak"
  }},
  "memory_keeper": {{
    "relevant_memories": ["memory summaries"],
    "context": "how memories inform current situation"
  }},
  "spatial_reasoner": {{
    "visible_objects": ["objects they can see"],
    "reachable_objects": ["objects they can interact with"],
    "current_observations": "what they notice"
  }},
  "action_planner": {{
    "proposals": [
      {{"action": "action_type", "target": "object/location", "reasoning": "why"}},
      {{"action": "action_type", "target": "object/location", "reasoning": "why"}},
      {{"action": "action_type", "target": "object/location", "reasoning": "why"}}
    ]
  }},
  "validator": {{
    "selected_action": {{"action": "chosen action", "target": "target"}},
    "confidence": 0.85,
    "validation_reasoning": "why this action makes sense",
    "potential_issues": ["any concerns"]
  }},
  "response_message": "what {character_name} says/does (in character)"
}}
"""
```

### Object Creation Prompt
```python
CREATE_OBJECT_PROMPT = """
Create a small movable object based on this description: {user_description}

Requirements:
- Name: Short, descriptive name
- Description: 2-3 sentences for LLM context
- Initial State: Default state string
- Size: 1x1 or 2x1 cells (choose appropriate)
- Properties: movable, walkable, interactable flags
- Sprite Description: Simple 2-3 color icon description for pixel art

Output JSON:
{{
  "name": "Object Name",
  "description": "Detailed description for context",
  "initial_state": "state_string",
  "size": {{"width": 1, "height": 1}},
  "properties": {{
    "movable": true,
    "walkable": false,
    "interactable": true
  }},
  "sprite_description": "simple pixel art icon description"
}}
"""
```

## Testing Strategy

### Unit Tests
- Persona card parsing
- Pathfinding algorithm
- Brain council prompt generation
- Memory storage/retrieval
- Object state management

### Integration Tests
- LLM provider connections
- Database operations
- WebSocket communication
- Action execution pipeline

### End-to-End Tests
- Full conversation flow
- Object creation and interaction
- Idle mode transitions
- Dream storage and retrieval
- Persona switching

### Performance Tests
- Memory usage under load
- Response time for brain council
- Grid rendering performance
- Database query optimization

## Security Considerations

1. **LLM Safety**:
   - Input sanitization
   - Output filtering
   - Rate limiting on API calls
   - Token budget management

2. **Data Privacy**:
   - Local storage of conversations
   - Optional memory encryption
   - User data never leaves local system

3. **File System**:
   - Validate uploaded persona cards
   - Sandbox object creation
   - Limit file sizes

4. **API Security**:
   - CORS configuration
   - WebSocket authentication
   - Rate limiting

## Future Enhancements (Post-MVP)

1. **Multiple Rooms**: Different environments (office, bedroom, kitchen)
2. **Needs System**: Hunger, energy, social needs affect behavior
3. **Voice Integration**: TTS/STT support
4. **Multi-Assistant**: Multiple personas in same room
5. **Events System**: Scheduled events (alarms, reminders)
6. **Weather Integration**: Real weather affects room (rain on window)
7. **Time-of-Day**: Dynamic lighting based on real time
8. **Achievements**: Gamification elements
9. **Mod Support**: Community-created objects and rooms
10. **Cloud Sync**: Optional backup to cloud storage

## Success Metrics

- **Responsiveness**: Actions complete in <3 seconds
- **Memory Accuracy**: Relevant context retrieved >90% of time
- **Character Consistency**: Responses feel in-character >95% of time
- **Stability**: <1 crash per week of continuous use
- **Performance**: <500MB RAM usage, <10% CPU when idle

## Getting Started (For Claude Code)

1. **Initialize Repository**
   ```bash
   git init
   git remote add origin https://github.com/yourbr0ther/DeskMate.git
   ```

2. **Create Initial Structure**
   ```bash
   mkdir -p backend/app/{models,services,api,db,utils}
   mkdir -p frontend/src/{components,hooks,stores,utils,types}
   mkdir -p data/{personas,sprites/objects,sprites/expressions,rooms}
   mkdir -p docs
   ```

3. **Start with Phase 1**
   - Set up Docker Compose
   - Create FastAPI backend skeleton
   - Connect to Qdrant
   - Basic health checks

4. **Iterative Development**
   - Complete one phase before moving to next
   - Test thoroughly at each phase
   - Document as you go
   - Commit regularly

## Notes for Implementation

- **Persona Cards**: Use `Pillow` to extract PNG metadata chunks (tEXt/iTXt)
- **Grid Rendering**: Consider using HTML5 Canvas for performance with 64x16 cells
- **Pathfinding**: Implement A* with priority queue, cache common paths
- **Brain Council**: Use streaming for faster response, show "thinking" indicator
- **Memory**: Use hybrid search (semantic + keyword) for best retrieval
- **Idle Mode**: Implement exponential backoff for action frequency
- **Docker**: Use multi-stage builds to reduce image size
- **WebSocket**: Implement reconnection logic with exponential backoff

## Open Questions for Development

1. Should assistant be able to leave the room (through door)?
2. Should time pass differently in idle mode (faster)?
3. Should there be seasonal room variations?
4. Should objects have durability/wear over time?
5. Should assistant have a backstory that develops over time?

---

**Version**: 1.1
**Last Updated**: 2025-12-02
**Status**: Phase 11 Complete - Phase 12 In Progress
**Estimated Timeline**: 24 weeks (6 months)

### Implementation Progress:
- **Phases 1-11**: Complete
- **Phase 12**: In Progress (Multi-Device & Advanced Features)
