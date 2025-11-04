# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeskMate is a virtual AI companion that lives in a simulated room environment on a 1920x480 secondary monitor. The companion uses LLM technology and SillyTavern-compatible persona cards to create an interactive desktop assistant.

## Current Status

**Phase 1-10: COMPLETE ✅** - Foundation through UI/UX Polish
**Current**: Phase 10 complete with comprehensive settings, enhanced UI, and performance monitoring
**Next**: Phase 11 - Testing & Documentation

### Completed Phases:
- ✅ **Phase 1**: Foundation & Infrastructure (Docker, FastAPI, databases)
- ✅ **Phase 2**: Persona System & Basic Frontend (SillyTavern V2 support)
- ✅ **Phase 3**: Room Environment & Objects (64x16 grid, object management)
- ✅ **Phase 4**: Assistant Movement & Pathfinding (A* algorithm)
- ✅ **Phase 5**: LLM Integration (Nano-GPT + Ollama dual provider)
- ✅ **Phase 6**: Chat System & Memory (conversation memory, vector search)
- ✅ **Phase 7**: Brain Council System (multi-perspective AI reasoning, action execution)
- ✅ **Phase 8**: Object Manipulation & Interaction (pick up, put down, visual feedback)
- ✅ **Phase 9**: Idle Mode & Autonomous Behavior (10-minute timeout, lightweight models, dream storage)
- ✅ **Phase 10**: UI/UX Polish & Improvements (settings panel, time display, status indicators, expression transitions, performance monitoring)

## Git Repository

- **Remote**: https://github.com/YourBr0ther/deskmate.git
- **Branch**: main
- **Latest Commit**: Phase 7 complete with Brain Council System and Action Execution

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
# Phase 10 UI/UX Polish Testing
./test_phase10_ui_polish.sh               # Comprehensive UI/UX test suite
python3 test_phase10_interactive.py       # Interactive UI/UX testing guide

# Phase 9 Idle Mode Testing
./test_phase9_idle_mode.sh                # Comprehensive idle mode test suite

# Phase 8 Object Manipulation Testing
./test_phase8_object_manipulation.sh      # Comprehensive object manipulation test suite
python3 test_object_manipulation_interactive.py  # Interactive object manipulation testing

# Phase 7 Brain Council Testing
./test_phase7.sh                    # Comprehensive Brain Council test suite
./test_movement_visual.sh           # Visual movement test
python3 test_websocket_interactive.py  # Interactive WebSocket test

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
curl http://localhost:8000/health     # Health check
curl http://localhost:8000/brain/test # Brain Council test
```

### Memory Management Commands

```bash
# API endpoints for memory clearing
curl -X POST http://localhost:8000/conversation/memory/clear          # Clear current
curl -X POST http://localhost:8000/conversation/memory/clear-all      # Clear all (DESTRUCTIVE)
curl -X POST "http://localhost:8000/conversation/memory/clear-persona?persona_name=Alice"  # Clear persona

# Memory analysis
curl -X POST http://localhost:8000/brain/analyze -H "Content-Type: application/json" -d '{"include_memory": true}'

# Frontend UI: Use trash icon in chat header for clearing options
```

## Architecture Overview

### Brain Council System (Phase 7)
DeskMate uses a novel "Brain Council" AI reasoning pattern where 5 specialized council members collaborate:
1. **Personality Core** - Maintains character consistency with active persona
2. **Memory Keeper** - Retrieves relevant context from vector DB and conversation history
3. **Spatial Reasoner** - Understands room layout, object visibility, and movement constraints
4. **Action Planner** - Proposes possible actions (movement, interaction, state changes)
5. **Validator** - Ensures actions make sense and are physically possible

The council returns structured JSON responses that drive both chat responses and room actions.

### Key Components

**Backend (Python/FastAPI):**
- `app/services/brain_council.py` - Multi-perspective AI reasoning system
- `app/services/action_executor.py` - Robust action execution pipeline
- `app/services/pathfinding.py` - A* algorithm for movement with obstacle avoidance
- `app/services/conversation_memory.py` - Qdrant vector DB integration with semantic search
- `app/services/llm_manager.py` - Dual LLM provider (Nano-GPT API and Ollama)
- `app/models/assistant.py` - Assistant state management and tracking
- `app/api/brain_council.py` - Brain Council API endpoints
- `app/api/websocket.py` - Real-time communication with Brain Council integration

**Frontend (React/TypeScript):**
- `src/components/Grid.tsx` - 64x16 room grid visualization (1920x480 @ 30px/cell)
- `src/stores/roomStore.ts` - Zustand state management for room objects and assistant
- `src/hooks/useWebSocket.ts` - Real-time WebSocket communication
- `src/components/Chat/` - Chat interface with streaming support

**Databases:**
- PostgreSQL - Metadata (objects, positions, states, assistant tracking)
- Qdrant - Vector storage (conversation memories with semantic search)

### Action Execution System

**Supported Actions:**
- **Movement**: Pathfinding with A* algorithm and obstacle avoidance
- **Object Interaction**: Activate, examine, use objects with state changes
- **State Changes**: Modify object properties (power, open/closed, etc.)
- **Expression Changes**: Update assistant mood and expression
- **Pick Up/Put Down**: Object manipulation (planned for Phase 8)

### Dual Mode Operation

**Active Mode:**
- Real-time chat with primary LLM (Nano-GPT or Ollama)
- User-driven interactions through Brain Council
- Full multi-perspective reasoning
- Immediate action execution

**Idle Mode:** (Planned for Phase 9)
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

### Object Manipulation APIs
- `POST /assistant/pick-up/{object_id}` - Pick up a movable object by ID
- `POST /assistant/put-down` - Put down held object (optional position in body)
- `GET /assistant/holding` - Check what object the assistant is holding

### Memory & Conversation
- `GET /conversation/memory/stats` - Memory statistics
- `POST /conversation/memory/clear` - Clear current conversation
- `GET /conversation/history` - Chat history for frontend

### WebSocket
- `WS /ws` - Real-time chat with Brain Council integration

## Testing Framework

### Phase 8 Verification
```bash
# Test object manipulation features
./test_phase8_object_manipulation.sh

# Interactive object manipulation testing
python3 test_object_manipulation_interactive.py
```

### Phase 7 Verification
```bash
# Test Brain Council reasoning
./test_phase7.sh

# Visual movement test (watch assistant move in grid)
./test_movement_visual.sh

# Interactive WebSocket testing
python3 test_websocket_interactive.py
```

### What to Test
1. **Object Manipulation** - Pick up, put down, and holding object tracking
2. **Visual Feedback** - Orange ring and 📦 icon when holding objects
3. **Distance Validation** - Proximity requirements for object manipulation
4. **Collision Detection** - Proper placement validation and boundary checks
5. **Brain Council Integration** - Object manipulation suggestions and reasoning
6. **API Endpoints** - Dedicated manipulation endpoints functionality
7. **Brain Council Reasoning** - Multi-perspective analysis in responses
8. **Action Generation** - Appropriate actions for user requests
9. **Memory Integration** - Context awareness from past conversations
10. **Movement Execution** - Pathfinding and grid position updates
11. **Object Interaction** - State changes and room updates
12. **Real-time Updates** - WebSocket synchronization

## Implementation Notes

### Current Working Features
1. **Multi-LLM Support** - Nano-GPT and Ollama with model switching
2. **Persona System** - SillyTavern V2 card support with PNG metadata
3. **Room Grid System** - 64x16 cells with object positioning
4. **Pathfinding** - A* algorithm with obstacle avoidance
5. **Conversation Memory** - Vector database with semantic search
6. **Brain Council** - 5-member reasoning system with action execution
7. **Real-time Chat** - WebSocket with streaming responses
8. **Object Management** - Create, position, and interact with room objects
9. **Object Manipulation** - Pick up, put down, and hold objects with visual feedback
10. **Collision Detection** - Smart placement validation and boundary checking
11. **Manipulation APIs** - Dedicated endpoints for object manipulation actions

### Development Priorities
1. **Phase 9**: Implement idle mode and autonomous behavior
2. **Phase 10**: Polish UI/UX and performance optimization
3. **Phase 11**: Comprehensive testing and documentation
4. **Phase 12**: Production deployment and advanced features

## Key Files to Reference

- `/Users/christophervance/deskmate/DESKMATE_SPEC.md` - Complete specification (39KB)
- Brain Council implementation in `backend/app/services/brain_council.py`
- Action execution in `backend/app/services/action_executor.py`
- WebSocket integration in `backend/app/api/websocket.py`
- Grid visualization in `frontend/src/components/Grid.tsx`

## Important Considerations

- **Target Resolution**: Exactly 1920x480 (kiosk mode for secondary monitor)
- **Grid System**: All objects and assistant fit in 64x16 grid
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
# This file exists and is already configured for local use
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

2. **Batch Tool Calls** - Always batch multiple independent operations (file reads, bash commands) in a single response to reduce message count.

3. **Selective File Reading** - Only read files directly related to the current task. Use Grep/Glob to find specific content rather than reading entire files.

4. **Incremental Development** - Focus on one phase/feature at a time. Complete and test before moving to the next.

### When Approaching Context Limit

**Early Warning Signs:**
- Working on multiple complex features simultaneously
- Reading many large files in succession
- Extensive debugging with multiple test runs
- Long conversation history

**Immediate Actions:**
1. Update this CLAUDE.md file with:
   - Current task in progress (exact feature/bug)
   - Files currently being modified
   - Test commands that need to be run
   - Next steps after context reset

2. Create a `CONTEXT_CHECKPOINT.md` file:
   ```markdown
   # Context Checkpoint - [Date]

   ## Current Task
   [Exact description of what you're implementing/fixing]

   ## Modified Files
   - path/to/file1.py - [what was changed]
   - path/to/file2.tsx - [what was changed]

   ## Completed Steps
   1. [What was accomplished]
   2. [What was tested]

   ## Next Steps
   1. [Immediate next action]
   2. [Following actions]

   ## Test Commands
   - `command to verify current work`
   - `command to run tests`

   ## Known Issues
   - [Any bugs or blockers encountered]
   ```

### After Context Reset

1. Read `CONTEXT_CHECKPOINT.md` first
2. Use Grep to quickly verify file states
3. Run test commands to confirm system state
4. Continue from documented next steps

### Best Practices

- **Always Rebuild for Testing** - Use `docker-compose down && docker-compose build --no-cache && docker-compose up -d` when testing changes
- **Write Incremental Commits** - Commit work regularly with descriptive messages
- **Update Todo List Frequently** - Keep todos current to track progress
- **Document Complex Logic** - Add comments for intricate implementations
- **Test After Each Feature** - Verify work before moving on
- **Use Phase Test Scripts** - Run phase-specific tests to verify functionality