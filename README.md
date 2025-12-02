# DeskMate - Virtual AI Companion

DeskMate is a virtual AI companion that lives in a simulated room environment. The companion uses LLM technology and persona cards (SillyTavern-compatible) to create an interactive, living desktop assistant with advanced multi-perspective AI reasoning, multi-room navigation, and responsive multi-device support.

## Project Status

**Current Phase**: Phase 12 In Progress - Multi-Device & Advanced Features

### Completed Phases:
- **Phase 1**: Foundation & Infrastructure (Docker, FastAPI, databases)
- **Phase 2**: Persona System & Basic Frontend (SillyTavern V2 support)
- **Phase 3**: Room Environment & Objects (grid system, object management)
- **Phase 4**: Assistant Movement & Pathfinding (A* algorithm)
- **Phase 5**: LLM Integration (Nano-GPT + Ollama dual provider)
- **Phase 6**: Chat System & Memory (conversation memory, vector search)
- **Phase 7**: Brain Council System (multi-perspective AI reasoning, action execution)
- **Phase 8**: Object Manipulation & Interaction (pick up, put down, visual feedback)
- **Phase 9**: Idle Mode & Autonomous Behavior (10-minute timeout, dreams)
- **Phase 10**: UI/UX Polish & Improvements (settings, status indicators, performance monitoring)
- **Phase 11**: Testing & Documentation (comprehensive test suites)

### Current Work (Phase 12):
- Multi-device responsive design (desktop/tablet/mobile)
- Top-down SVG floor plan rendering
- Multi-room navigation with doorways

### Features Available:
- **Brain Council Reasoning**: 5-member AI council for contextual decision making
- **Real-time chat** with streaming AI responses and action execution
- **SillyTavern persona cards** with PNG metadata support
- **Multi-room environment** with floor plans, doorways, and furniture
- **Assistant movement** with A* pathfinding and multi-room navigation
- **Object manipulation**: Pick up, put down, and hold objects
- **Idle mode**: Autonomous behavior with "dreams" when inactive
- **Model switching** between Ollama (local) and Nano-GPT (cloud)
- **Conversation memory** with semantic search and context retrieval
- **Responsive UI** with desktop, tablet, and mobile layouts
- **Settings panel** with comprehensive configuration options
- **Performance monitoring** with FPS and system metrics

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

### Testing

```bash
# Backend tests
cd backend
pytest -v
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test
npm run lint
npm run typecheck
```

## Architecture

### Brain Council System
DeskMate features a unique **Brain Council** AI reasoning system where 5 specialized council members collaborate:

1. **Personality Core** - Maintains character consistency with active persona
2. **Memory Keeper** - Retrieves relevant context from vector database
3. **Spatial Reasoner** - Understands room layout and object visibility
4. **Action Planner** - Proposes contextual actions (movement, interaction)
5. **Validator** - Ensures actions are safe and physically possible

The council generates structured JSON responses that drive both chat responses and room actions.

### Multi-Room System
The project uses a continuous pixel-based coordinate system for multi-room navigation:
- **Floor Plans** - Container for multiple rooms, walls, doorways, furniture
- **Rooms** - Individual spaces with bounds and styling
- **Doorways** - Connections between rooms with accessibility states
- **Furniture** - Objects positioned with continuous coordinates

### Responsive Layout System
- **Desktop (1920x1080+)**: Split layout - 70% floor plan, 30% chat panel
- **Tablet (769-1024px)**: Stacked layout with collapsible chat
- **Mobile (<768px)**: Full-screen floor plan with floating chat widget

### Technology Stack

**Backend (Python/FastAPI):**
- **FastAPI** with async WebSocket support for real-time communication
- **Brain Council** multi-perspective AI reasoning system (modular architecture)
- **Action Executor** for movement, interaction, and state management
- **Multi-room pathfinding** with A* algorithm and doorway transitions
- **PostgreSQL** for metadata (floor plans, rooms, furniture, assistant state)
- **Qdrant** vector database for conversation memory and dreams
- **Dual LLM Support**: Nano-GPT (cloud) + Ollama (local models)
- **Idle Controller** for autonomous behavior

**Frontend (React/TypeScript):**
- **React 18** with TypeScript and modern hooks
- **Zustand** unified state management (spatialStore)
- **WebSocket** real-time communication with auto-reconnection
- **Tailwind CSS** responsive design for mobile, tablet, and desktop
- **SVG Floor Plan Renderer** for multi-room visualization

**Databases & Services:**
- **PostgreSQL** - Floor plans, rooms, furniture, assistant state
- **Qdrant** - Vector embeddings for conversation memory and dreams
- **Docker Compose** - Multi-container orchestration

## API Documentation

### Core Endpoints
- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs` (Swagger/OpenAPI)

### Brain Council APIs
- **Test Council**: `GET /brain/test`
- **Process Message**: `POST /brain/process`
- **Analyze Context**: `POST /brain/analyze`

### Room Navigation APIs
- **List Floor Plans**: `GET /room/floor-plans`
- **Current Room**: `GET /room/current`
- **Navigate**: `POST /room/navigate`
- **Doorway Transition**: `POST /room/doorway/transition`

### Object Manipulation APIs
- **Pick Up Object**: `POST /assistant/pick-up/{object_id}`
- **Put Down Object**: `POST /assistant/put-down`
- **Check Holding**: `GET /assistant/holding`

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
   - "Pick up the book"
   - "What objects can you see?"

### Dual Mode Operation

**Active Mode:**
- Real-time chat with primary LLM
- User-driven interactions through Brain Council
- Full multi-perspective reasoning

**Idle Mode:**
- Triggers after 10 minutes of inactivity
- Uses lightweight Ollama models
- Autonomous actions stored as "dreams"
- Dreams expire after 24 hours

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

# Test Brain Council
curl http://localhost:8000/brain/test
```

**WebSocket connection failed:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check Docker containers
docker-compose ps
```

**Assistant not moving:**
```bash
# Test pathfinding
curl -X POST http://localhost:8000/brain/process \
  -H "Content-Type: application/json" \
  -d '{"message": "Move to the desk"}'
```

**Database connection issues:**
```bash
# Restart databases
docker-compose restart deskmate-postgres deskmate-qdrant

# Check database status
docker exec -it deskmate-postgres psql -U deskmate -d deskmate
curl http://localhost:6333/collections
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Developer guidance and current state
- **[DESKMATE_SPEC.md](DESKMATE_SPEC.md)** - Complete project specification
- **[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** - Technical developer documentation
- **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Installation and setup guide
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - User documentation

## Contributing

This project uses:
- **Conventional Commits** for clear commit messages
- **Automated Co-authoring** with Claude Code
- **Phase-based Development** following the specification
- **Comprehensive Testing** before feature completion

See [DESKMATE_SPEC.md](DESKMATE_SPEC.md) for complete development roadmap.

## License

[License information to be added]

---

**Ready to chat with your AI companion? Start Docker and visit http://localhost:3000!**
