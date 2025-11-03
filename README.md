# DeskMate - Virtual AI Companion

DeskMate is a virtual AI companion that lives in a simulated room environment displayed on a secondary 1920x480 monitor. The companion uses LLM technology and persona cards (SillyTavern-compatible) to create an interactive, living desktop assistant.

## Project Status

**Current Phase**: Phase 5 & 6 - LLM Integration & Chat System (Complete)
- ✅ Phase 1: Foundation & Infrastructure
- ✅ Phase 2: Persona System & Basic Frontend
- ✅ Phase 3: Room Environment & Grid System
- ✅ Phase 4: Assistant System & Movement
- ✅ Phase 5: LLM Integration (Ollama + Nano-GPT)
- ✅ Phase 6: Chat System & WebSocket Communication

**Features Available:**
- 🤖 Real-time chat with AI assistants
- 🎭 SillyTavern persona card support
- 🏠 Interactive room environment (64x16 grid)
- 🚶 Assistant movement and pathfinding
- 🔄 Model switching (Ollama & cloud LLMs)
- 📱 Responsive mobile/desktop UI

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ollama (for local LLM models) - Optional, can use cloud LLMs
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- Git (for version control)

### Running with Docker

1. Clone the repository:
```bash
git clone https://github.com/YourBr0ther/deskmate.git
cd deskmate
```

2. Start all services:
```bash
docker-compose up -d
```

3. Check service health:
```bash
curl http://localhost:8000/health
```

4. Access the application:
```bash
# Frontend (React app)
open http://localhost:3000

# Backend API docs
open http://localhost:8000/docs
```

5. Set up Ollama (optional, for local models):
```bash
# Install and start Ollama
ollama serve

# Download a model (e.g., llama3.2)
ollama pull llama3.2:latest
```

### Local Development

1. Backend setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Run the backend:
```bash
uvicorn app.main:app --reload
```

### Running Tests

```bash
cd backend
pytest -v
```

## Architecture

- **Backend**: FastAPI (Python 3.11+) with WebSocket support
- **Frontend**: React 18 + TypeScript + Zustand state management
- **Databases**: PostgreSQL (metadata) + Qdrant (vector storage)
- **LLM Integration**: Ollama (local models) + Nano-GPT API (cloud models)
- **Communication**: WebSocket for real-time chat + REST APIs
- **Deployment**: Docker Compose with Nginx reverse proxy

## API Documentation

Once running, visit:
- **Frontend**: http://localhost:3000 (Main application)
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (Swagger/OpenAPI)
- **WebSocket**: ws://localhost:8000/ws (Real-time chat)

## Usage

1. **Select a Persona**: Click the persona selector to choose an AI character
2. **Chat Interface**: Use the chat panel to converse with your AI companion
3. **Room Interaction**: Click objects in the room grid to interact with them
4. **Assistant Movement**: Click empty spaces to move your assistant
5. **Model Switching**: Use the model selector to switch between LLM providers

## Development Phases

See [DESKMATE_SPEC.md](DESKMATE_SPEC.md) for the complete development roadmap.

## Git Workflow

### Repository Setup
- **Remote**: https://github.com/YourBr0ther/deskmate.git
- **Main Branch**: `main`
- **Current Status**: Phase 1 Complete

### Commit History
- **Phase 1**: Foundation & Infrastructure (Complete)
- All commits include automated co-authoring with Claude Code

### Development Commands
```bash
# Check repository status
git status

# View commit history
git log --oneline

# Push to remote (when ready)
git push -u origin main
```

## License

[License information to be added]