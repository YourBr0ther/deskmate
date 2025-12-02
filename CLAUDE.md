# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeskMate is a virtual AI companion that lives in a simulated room environment. The companion uses LLM technology and SillyTavern-compatible persona cards to create an interactive desktop assistant with multi-room navigation and responsive multi-device support.

## Current Status

**Phase 1-11: COMPLETE** - Foundation through Testing & Documentation
**Current**: Phase 12 - Multi-Device & Advanced Features (In Progress)

### Completed Phases:
- **Phase 1**: Foundation & Infrastructure (Docker, FastAPI, databases)
- **Phase 2**: Persona System & Basic Frontend (SillyTavern V2 support)
- **Phase 3**: Room Environment & Objects (grid system, object management)
- **Phase 4**: Assistant Movement & Pathfinding (A* algorithm)
- **Phase 5**: LLM Integration (Nano-GPT + Ollama dual provider)
- **Phase 6**: Chat System & Memory (conversation memory, vector search)
- **Phase 7**: Brain Council System (multi-perspective AI reasoning, action execution)
- **Phase 8**: Object Manipulation & Interaction (pick up, put down, visual feedback)
- **Phase 9**: Idle Mode & Autonomous Behavior (10-minute timeout, lightweight models, dream storage)
- **Phase 10**: UI/UX Polish & Improvements (settings panel, time display, status indicators, expression transitions, performance monitoring)
- **Phase 11**: Testing & Documentation (comprehensive test suites, 80%+ coverage targets)

### Current Work (Phase 12):
- Multi-device responsive design (desktop/tablet/mobile layouts)
- Top-down SVG floor plan rendering
- Multi-room navigation with doorways
- Floating chat widget for mobile

## Git Repository

- **Remote**: https://github.com/YourBr0ther/deskmate.git
- **Branch**: main

## Development Commands

### Docker Development (Recommended)

**Full rebuild for development testing:**
```bash
# Stop services and rebuild completely (ensures clean testing environment)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Quick restart (when only code changes, no dependencies)
docker-compose restart deskmate-backend deskmate-frontend

# View logs during development
docker-compose logs -f deskmate-backend
docker-compose logs -f deskmate-frontend

# Clean shutdown
docker-compose down
```

**Development workflow with rebuilds:**
```bash
# Make code changes, then rebuild and test
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Quick check if services are running
docker-compose ps

# Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Backend Docs: http://localhost:8000/docs
```

### Local Development (Alternative)

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend setup
cd frontend
npm install
npm run dev  # Development server at http://localhost:3000

# Databases (requires Docker)
docker-compose up -d deskmate-postgres deskmate-qdrant
```

### Testing Commands

```bash
# Backend tests
cd backend
pytest -v
pytest --cov=app tests/

# Frontend tests
cd frontend
npm run test
npm run lint
npm run typecheck

# API testing
curl http://localhost:8000/health
curl http://localhost:8000/brain/test
```

### Memory Management Commands

```bash
# API endpoints for memory clearing
curl -X POST http://localhost:8000/conversation/memory/clear
curl -X POST http://localhost:8000/conversation/memory/clear-all
curl -X POST "http://localhost:8000/conversation/memory/clear-persona?persona_name=Alice"

# Memory analysis
curl -X POST http://localhost:8000/brain/analyze -H "Content-Type: application/json" -d '{"include_memory": true}'
```

## Architecture Overview

### Brain Council System
DeskMate uses a "Brain Council" AI reasoning pattern where 5 specialized council members collaborate:
1. **Personality Core** - Maintains character consistency with active persona
2. **Memory Keeper** - Retrieves relevant context from vector DB and conversation history
3. **Spatial Reasoner** - Understands room layout, object visibility, and movement constraints
4. **Action Planner** - Proposes possible actions (movement, interaction, state changes)
5. **Validator** - Ensures actions make sense and are physically possible

The council returns structured JSON responses that drive both chat responses and room actions.

### Key Components

**Backend (Python/FastAPI):**
- `app/services/brain_council/` - Modular multi-perspective AI reasoning system
- `app/services/action_executor.py` - Robust action execution pipeline
- `app/services/multi_room_pathfinding.py` - A* algorithm for multi-room movement
- `app/services/conversation_memory.py` - Qdrant vector DB integration with semantic search
- `app/services/llm_manager.py` - Dual LLM provider (Nano-GPT API and Ollama)
- `app/services/idle_controller.py` - Autonomous idle behavior
- `app/services/dream_memory.py` - Dream storage for idle mode
- `app/services/room_navigation.py` - Multi-room movement logic
- `app/models/floor_plans.py` - Floor plan, room, wall, doorway models
- `app/api/websocket.py` - Real-time communication with Brain Council integration

**Frontend (React/TypeScript):**
- `src/stores/spatialStore.ts` - Unified state management for rooms, objects, assistant
- `src/components/FloorPlan/TopDownRenderer.tsx` - SVG-based multi-room floor plan
- `src/components/Layout/` - Responsive layouts (Desktop, Tablet, Mobile)
- `src/components/Chat/FloatingChatWidget.tsx` - Mobile floating chat
- `src/hooks/useWebSocketIntegration.ts` - Real-time WebSocket communication
- `src/hooks/useRoomNavigation.ts` - Multi-room navigation logic
- `src/hooks/useDeviceDetection.ts` - Device type detection
- `src/components/Settings/SettingsPanel.tsx` - Comprehensive settings UI

**Databases:**
- PostgreSQL - Metadata (floor plans, rooms, furniture, assistant state)
- Qdrant - Vector storage (conversation memories, dreams)

### Multi-Room System

The project uses a continuous pixel-based coordinate system for multi-room navigation:
- **Floor Plans** - Container for multiple rooms, walls, doorways, furniture
- **Rooms** - Individual spaces within a floor plan with bounds and styling
- **Doorways** - Connections between rooms with accessibility states
- **Furniture** - Objects positioned with continuous coordinates

### Responsive Layout System

- **Desktop (1920x1080+)**: Split layout - 70% floor plan, 30% chat panel
- **Tablet (769-1024px)**: Stacked layout with collapsible chat
- **Mobile (<768px)**: Full-screen floor plan with floating chat widget

### Dual Mode Operation

**Active Mode:**
- Real-time chat with primary LLM (Nano-GPT or Ollama)
- User-driven interactions through Brain Council
- Full multi-perspective reasoning
- Immediate action execution

**Idle Mode:**
- Triggers after 10 minutes inactivity or `/idle` command
- Uses lightweight Ollama models (phi-3, gemma-2b)
- Autonomous actions based on goals and environment
- Actions stored as "dreams" that expire after 24 hours

## API Endpoints

### Core APIs
- `GET /health` - System health check
- `GET /chat/models` - Available LLM models
- `POST /chat/simple` - Quick chat testing

### Brain Council APIs
- `GET /brain/test` - Test Brain Council functionality
- `POST /brain/process` - Process message through Brain Council
- `POST /brain/analyze` - Analyze current context and memory

### Room Navigation APIs
- `GET /room/floor-plans` - List available floor plans
- `POST /room/floor-plans` - Create floor plan
- `GET /room/current` - Get current room state
- `POST /room/navigate` - Navigate to position/room
- `POST /room/doorway/transition` - Transition through doorway

### Object Manipulation APIs
- `POST /assistant/pick-up/{object_id}` - Pick up a movable object by ID
- `POST /assistant/put-down` - Put down held object
- `GET /assistant/holding` - Check what object the assistant is holding

### Memory & Conversation
- `GET /conversation/memory/stats` - Memory statistics
- `POST /conversation/memory/clear` - Clear current conversation
- `GET /conversation/history` - Chat history for frontend

### WebSocket
- `WS /ws` - Real-time chat with Brain Council integration

## Key Files to Reference

- `DESKMATE_SPEC.md` - Complete specification
- `docs/DEVELOPER_GUIDE.md` - Developer documentation
- `docs/PHASE_12B_MULTI_DEVICE_SPEC.md` - Multi-device implementation spec
- `TECHNICAL_DEBT_PHASES.md` - Technical debt reduction plan
- Brain Council: `backend/app/services/brain_council/`
- Action execution: `backend/app/services/action_executor.py`
- WebSocket integration: `backend/app/api/websocket.py`
- Spatial state: `frontend/src/stores/spatialStore.ts`
- Floor plan rendering: `frontend/src/components/FloorPlan/TopDownRenderer.tsx`

## Important Considerations

- **Responsive Design**: Supports desktop, tablet, and mobile layouts
- **Multi-Room System**: Floor plans with multiple connected rooms
- **Coordinate System**: Continuous pixel-based positioning
- **Persona Compatibility**: Maintain SillyTavern V2 format support
- **Memory Efficiency**: Use vector search for relevant context retrieval
- **Real-time Updates**: All actions broadcast via WebSocket
- **Security**: Never commit API keys or sensitive credentials

## Environment Variables

**Required for Backend:**
```bash
NANO_GPT_API_KEY=your_api_key_here  # Get from nano-gpt.com
OLLAMA_URL=http://localhost:11434   # Local Ollama instance
DATABASE_URL=postgresql://...       # PostgreSQL connection
QDRANT_URL=http://localhost:6333    # Qdrant vector database
```

**Docker Compose handles all database URLs automatically**

**Setting API Key:**
```bash
# Method 1: Environment variable (recommended for CI/CD)
export NANO_GPT_API_KEY="your_api_key_here"

# Method 2: Create .env.local file (gitignored)
echo "NANO_GPT_API_KEY=your_api_key_here" > .env.local

# Method 3: Update backend/.env for local development (gitignored)
```

## Troubleshooting

### Common Issues
1. **API Key Issues**: Check docker-compose.yml and ensure key is set
2. **Database Connection**: Ensure PostgreSQL and Qdrant containers are running
3. **WebSocket Errors**: Check browser console and backend logs
4. **Movement Issues**: Verify pathfinding and obstacle detection
5. **Memory Issues**: Check Qdrant connection and embedding generation

### Debug Commands
```bash
# Check service status
docker-compose ps

# View real-time logs
docker-compose logs -f deskmate-backend

# Test individual components
curl http://localhost:8000/brain/test
curl http://localhost:8000/conversation/memory/stats

# Database connections
docker exec -it deskmate-postgres psql -U deskmate -d deskmate
curl http://localhost:6333/collections
```

## Context Window Management

### Prevention Strategies

1. **Use Task Tool for Large Searches** - When searching through multiple files or doing complex analysis, use the Task tool with the general-purpose agent to minimize context usage.

2. **Batch Tool Calls** - Always batch multiple independent operations in a single response.

3. **Selective File Reading** - Only read files directly related to the current task.

4. **Incremental Development** - Focus on one phase/feature at a time.

### Best Practices

- **Always Rebuild for Testing** - Use `docker-compose down && docker-compose build --no-cache && docker-compose up -d`
- **Write Incremental Commits** - Commit work regularly with descriptive messages
- **Update Todo List Frequently** - Keep todos current to track progress
- **Document Complex Logic** - Add comments for intricate implementations
- **Test After Each Feature** - Verify work before moving on
