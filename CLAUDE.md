# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeskMate is a virtual AI companion that lives in a simulated room environment on a 1920x480 secondary monitor. The companion uses LLM technology and SillyTavern-compatible persona cards to create an interactive desktop assistant.

## Current Status

This is a greenfield project - only the specification exists. Implementation should follow the 24-week development plan starting with Phase 1.

## Development Commands

Since no code exists yet, here are the commands to use during development:

### Initial Setup
```bash
# Create project structure
mkdir -p backend/app/{models,services,api,db,utils}
mkdir -p frontend/src/{components,hooks,stores,utils,types}
mkdir -p data/{personas,sprites/objects,sprites/expressions,rooms}
mkdir -p docs

# Backend setup (once created)
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend setup (once created)
cd frontend
npm install
npm run dev  # Development server
npm run electron:dev  # Electron development (1920x480 kiosk)
npm run build
npm run test

# Docker setup
docker-compose up -d  # Start all services
docker-compose logs -f  # View logs
docker-compose down  # Stop services
```

### Testing Commands
```bash
# Backend tests
cd backend
pytest -v
pytest --cov=app tests/  # With coverage

# Frontend tests
cd frontend
npm run test
npm run test:e2e  # Playwright tests

# Linting
cd backend
ruff check .
mypy app/

cd frontend
npm run lint
npm run typecheck
```

## Architecture Overview

### Brain Council System
DeskMate uses a novel "Brain Council" AI reasoning pattern where 5 specialized council members collaborate:
1. **Personality Core** - Maintains character consistency
2. **Memory Keeper** - Retrieves relevant context from vector DB
3. **Spatial Reasoner** - Understands room layout and object visibility
4. **Action Planner** - Proposes possible actions
5. **Validator** - Ensures actions make sense

The council returns structured JSON responses that drive assistant behavior.

### Key Components

**Backend (Python/FastAPI):**
- `app/services/brain_council.py` - Multi-perspective AI reasoning
- `app/services/pathfinding.py` - A* algorithm for movement
- `app/services/memory.py` - Qdrant vector DB integration
- `app/services/llm_manager.py` - Handles Nano-GPT API and Ollama
- `app/models/persona.py` - SillyTavern V2 persona card parsing

**Frontend (React/Electron):**
- `src/components/Grid.tsx` - 64x16 room grid (1920x480 @ 30px/cell)
- `src/components/Companion.tsx` - 640x480 companion panel
- `src/stores/roomStore.ts` - Zustand state for objects/assistant
- `src/hooks/useWebSocket.ts` - Real-time communication

**Databases:**
- PostgreSQL - Metadata (objects, positions, states)
- Qdrant - Vector storage (memories, dreams)

### Dual Mode Operation

**Active Mode:**
- Real-time chat with primary LLM
- User-driven interactions
- Full brain council reasoning

**Idle Mode:**
- Triggers after 10 minutes inactivity or `/idle` command
- Uses lightweight Ollama models (phi-3, gemma-2b)
- Slower autonomous actions (1 per 2-5 minutes)
- Actions stored as "dreams" that expire after 24 hours

## Implementation Notes

1. **Start with Phase 1** - Docker setup, basic FastAPI, database connections
2. **Persona Cards** - Use Pillow to extract PNG tEXt/iTXt chunks for SillyTavern V2 format
3. **Grid Rendering** - Consider HTML5 Canvas for performance
4. **Pathfinding** - Cache common paths, use priority queue
5. **Memory Search** - Implement hybrid semantic + keyword search
6. **WebSocket** - Add reconnection logic with exponential backoff
7. **Object States** - Simple strings like "open/closed", "on/off", "red/blue"

## Key Files to Reference

- `/Users/christophervance/deskmate/DESKMATE_SPEC.md` - Complete 39KB specification
- Review Phase 1-12 development plan in spec before implementing features
- Brain Council prompt structure and JSON schema in spec
- Object creation prompt template in spec

## Important Considerations

- Target resolution is exactly 1920x480 (kiosk mode)
- All objects must fit in 64x16 grid system
- Maintain SillyTavern V2 compatibility for personas
- Keep idle mode lightweight for continuous operation
- Dreams are separate from real memories in Qdrant

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

- **Write Incremental Commits** - Even if not pushing, commit work regularly with descriptive messages
- **Update Todo List Frequently** - Keep todos current to track progress
- **Document Complex Logic** - Add comments for intricate implementations
- **Test After Each Feature** - Verify work before moving on