# DeskMate - Virtual AI Companion

DeskMate is a virtual AI companion that lives in a simulated room environment displayed on a secondary 1920x480 monitor. The companion uses LLM technology and persona cards (SillyTavern-compatible) to create an interactive, living desktop assistant with advanced multi-perspective AI reasoning.

## Project Status

**Current Phase**: Phase 7 Complete - Brain Council System with Action Execution
- ✅ **Phase 1**: Foundation & Infrastructure (Docker, FastAPI, databases)
- ✅ **Phase 2**: Persona System & Basic Frontend (SillyTavern V2 support)
- ✅ **Phase 3**: Room Environment & Objects (64x16 grid, object management)
- ✅ **Phase 4**: Assistant Movement & Pathfinding (A* algorithm)
- ✅ **Phase 5**: LLM Integration (Nano-GPT + Ollama dual provider)
- ✅ **Phase 6**: Chat System & Memory (conversation memory, vector search)
- ✅ **Phase 7**: Brain Council System (multi-perspective AI reasoning, action execution)

**Next Phase**: Phase 8 - Enhanced Object Manipulation & Interaction

**Features Available:**
- 🧠 **Brain Council Reasoning**: 5-member AI council for contextual decision making
- 🤖 **Real-time chat** with streaming AI responses and action execution
- 🎭 **SillyTavern persona cards** with PNG metadata support
- 🏠 **Interactive room environment** (64x16 grid) with object states
- 🚶 **Assistant movement** with A* pathfinding and obstacle avoidance
- 🔄 **Model switching** between Ollama (local) and Nano-GPT (cloud)
- 💾 **Conversation memory** with semantic search and context retrieval
- 📱 **Responsive mobile/desktop UI** with real-time updates
- ⚡ **Action execution** (movement, object interaction, state changes)

## Quick Start

### Prerequisites

- **Docker and Docker Compose** (required)
- **Nano-GPT API Key** (for cloud LLM) - Get from [nano-gpt.com](https://nano-gpt.com)
- **Ollama** (optional, for local models) - Download from [ollama.ai](https://ollama.ai)
- **Git** for cloning the repository

### Running with Docker (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/YourBr0ther/deskmate.git
cd deskmate
```

2. **Set up API key:**
```bash
# Set your Nano-GPT API key as environment variable
export NANO_GPT_API_KEY="your_api_key_here"

# OR create a .env.local file in the root directory
echo "NANO_GPT_API_KEY=your_api_key_here" > .env.local
```

3. **Start all services:**
```bash
# Full rebuild for clean environment (recommended for development)
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Quick start (if no changes to dependencies)
docker-compose up -d
```

4. **Verify services are running:**
```bash
# Check service status
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test Brain Council
curl http://localhost:8000/brain/test
```

5. **Access the application:**
- **Frontend**: http://localhost:3000 (Main DeskMate interface)
- **Backend API Docs**: http://localhost:8000/docs (Swagger/OpenAPI)
- **Brain Council API**: http://localhost:8000/brain/analyze

### Local Development Setup

For development without Docker:

1. **Backend setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn app.main:app --reload --port 8000
```

2. **Frontend setup:**
```bash
cd frontend
npm install
npm run dev  # Development server on port 3000
```

3. **Database setup (requires Docker):**
```bash
# Start only databases
docker-compose up -d deskmate-postgres deskmate-qdrant
```

#### Phase 7 Brain Council Tests
```bash
# Comprehensive Brain Council test suite
./test_phase7.sh

# Visual movement test (watch assistant move)
./test_movement_visual.sh

# Interactive WebSocket testing
python3 test_websocket_interactive.py
```

#### Backend Tests
```bash
cd backend
pytest -v                              # All tests
pytest tests/test_pathfinding.py -v    # Movement tests
pytest tests/test_websocket.py -v      # WebSocket tests
pytest --cov=app tests/                # With coverage
```

#### Frontend Tests
```bash
cd frontend
npm test        # Jest tests
npm run lint    # ESLint
npm run typecheck  # TypeScript validation
```

## Architecture

### Brain Council System (Phase 7)
DeskMate features a unique **Brain Council** AI reasoning system where 5 specialized council members collaborate:

1. **Personality Core** - Maintains character consistency with active persona
2. **Memory Keeper** - Retrieves relevant context from vector database
3. **Spatial Reasoner** - Understands room layout and object visibility
4. **Action Planner** - Proposes contextual actions (movement, interaction)
5. **Validator** - Ensures actions are safe and physically possible

The council generates structured JSON responses that drive both chat responses and real-world actions.

### Technology Stack

**Backend (Python/FastAPI):**
- **FastAPI** with async WebSocket support for real-time communication
- **Brain Council** multi-perspective AI reasoning system
- **Action Executor** for movement, interaction, and state management
- **PostgreSQL** for metadata (objects, positions, assistant state)
- **Qdrant** vector database for conversation memory and semantic search
- **Dual LLM Support**: Nano-GPT (cloud) + Ollama (local models)

**Frontend (React/TypeScript):**
- **React 18** with TypeScript and modern hooks
- **Zustand** state management for room, chat, and persona data
- **WebSocket** real-time communication with auto-reconnection
- **Tailwind CSS** responsive design for mobile and desktop
- **Grid System** 64x16 cell visualization (1920x480 target resolution)

**Databases & Services:**
- **PostgreSQL** - Object states, assistant tracking, room metadata
- **Qdrant** - Vector embeddings for semantic memory search
- **Docker Compose** - Multi-container orchestration

## API Documentation

### Core Endpoints
- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs` (Swagger/OpenAPI)

### Brain Council APIs
- **Test Council**: `GET /brain/test`
- **Process Message**: `POST /brain/process`
- **Analyze Context**: `POST /brain/analyze`

### Chat & Memory
- **WebSocket Chat**: `WS /ws`
- **Memory Stats**: `GET /conversation/memory/stats`
- **Clear Memory**: `POST /conversation/memory/clear`

### LLM Management
- **Available Models**: `GET /chat/models`
- **Model Selection**: `POST /chat/model/select`
- **Simple Chat**: `POST /chat/simple`

## Usage Guide

### Getting Started
1. **Select a Persona**: Choose an AI character from the persona selector
2. **Chat Interface**: Converse with your AI companion using natural language
3. **Room Interaction**: Watch the assistant move and interact with objects
4. **Action Commands**: Try phrases like:
   - "Move to the desk"
   - "Turn on the lamp"
   - "What objects can you see?"
   - "Walk to position 20, 10"

### Brain Council Features
- **Contextual Responses**: The AI considers room state, memory, and persona
- **Action Generation**: Requests automatically generate appropriate actions
- **Memory Integration**: Past conversations inform current responses
- **Multi-step Reasoning**: Complex requests are broken down intelligently

### Memory Management
```bash
# Clear current conversation
curl -X POST http://localhost:8000/conversation/memory/clear

# Clear all memory (destructive)
curl -X POST http://localhost:8000/conversation/memory/clear-all

# Clear specific persona memory
curl -X POST "http://localhost:8000/conversation/memory/clear-persona?persona_name=Alice"
```

## Development

### Development Workflow
```bash
# Make changes to code
# Always rebuild for testing to ensure clean environment
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# View logs during development
docker-compose logs -f deskmate-backend
docker-compose logs -f deskmate-frontend

# Quick restart (for minor changes)
docker-compose restart deskmate-backend
```

### Adding New Features
1. **Update appropriate service** (brain_council.py, action_executor.py, etc.)
2. **Add tests** for new functionality
3. **Test with Brain Council** using test scripts
4. **Update documentation** in CLAUDE.md
5. **Commit with descriptive message**

### Environment Variables
```bash
# Required
NANO_GPT_API_KEY=your_api_key_here

# Optional (handled by Docker Compose)
DATABASE_URL=postgresql://deskmate:deskmate@localhost:5432/deskmate
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434
```

## Troubleshooting

### Common Issues

**Brain Council not responding:**
```bash
# Check API key is set
echo $NANO_GPT_API_KEY

# Test LLM connection
curl http://localhost:8000/chat/test/ollama
curl http://localhost:8000/brain/test
```

**WebSocket connection failed:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check Docker containers
docker-compose ps

# View logs
docker-compose logs deskmate-backend
```

**Assistant not moving:**
```bash
# Test pathfinding
curl -X POST http://localhost:8000/brain/process \
  -H "Content-Type: application/json" \
  -d '{"message": "Move to position 10, 5"}'

# Check assistant state
curl http://localhost:8000/brain/analyze
```

**Database connection issues:**
```bash
# Restart databases
docker-compose restart deskmate-postgres deskmate-qdrant

# Check database status
docker exec -it deskmate-postgres psql -U deskmate -d deskmate
curl http://localhost:6333/collections
```

### Debug Commands
```bash
# Service status
docker-compose ps

# Real-time logs
docker-compose logs -f

# Database connections
docker exec -it deskmate-postgres psql -U deskmate -d deskmate
curl http://localhost:6333/collections

# API testing
curl http://localhost:8000/brain/test
curl http://localhost:8000/conversation/memory/stats
```

## Contributing

This project uses:
- **Conventional Commits** for clear commit messages
- **Automated Co-authoring** with Claude Code
- **Phase-based Development** following the specification
- **Comprehensive Testing** before feature completion

### Development Phases
- **Phase 1-7**: ✅ Complete (Foundation through Brain Council)
- **Phase 8**: 🔄 Object manipulation and advanced interaction
- **Phase 9**: 📋 Idle mode and autonomous behavior
- **Phase 10-12**: 📋 Polish, testing, and deployment

See [DESKMATE_SPEC.md](DESKMATE_SPEC.md) for complete development roadmap.

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Developer guidance and current state
- **[DESKMATE_SPEC.md](DESKMATE_SPEC.md)** - Complete project specification
- **[CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)** - Recent codebase cleanup notes

## License

[License information to be added]

---

**🚀 Ready to chat with your AI companion? Start Docker and visit http://localhost:3000!**