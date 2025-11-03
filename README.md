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

2. Frontend setup:
```bash
cd frontend
npm install
npm start  # Development server on port 3000
```

3. Run the backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

### Running Tests

```bash
# Backend tests
cd backend
pytest -v

# Test specific functionality
pytest tests/test_websocket.py -v  # WebSocket tests
pytest tests/test_pathfinding.py -v  # Movement tests
pytest tests/test_personas.py -v  # Persona tests

# Frontend tests (when implemented)
cd frontend
npm test
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

## Features

### 🤖 AI Companion System
- **SillyTavern Personas**: Load and chat with custom AI characters
- **Model Flexibility**: Switch between local (Ollama) and cloud (Nano-GPT) models
- **Streaming Responses**: Real-time message streaming for natural conversations
- **Memory System**: Vector-based memory storage for contextual conversations

### 🏠 Interactive Room Environment
- **64x16 Grid**: Pixel-perfect room layout designed for 1920x480 displays
- **Object Interaction**: Click furniture and objects to change their states
- **Assistant Movement**: A* pathfinding for realistic navigation
- **Real-time Updates**: WebSocket synchronization across all clients

### 🎭 Persona Management
- **PNG Metadata**: Extracts character data from SillyTavern V2 persona cards
- **Dynamic Loading**: Hot-swap between different AI personalities
- **Character Consistency**: Maintains persona traits across conversations

### 📱 Responsive Design
- **Desktop Layout**: Optimized for dual-monitor setups
- **Mobile Support**: Tab-based interface for mobile devices
- **Adaptive UI**: Automatically adjusts to screen size and orientation

## Usage

1. **Select a Persona**: Click the persona selector to choose an AI character
2. **Chat Interface**: Use the chat panel to converse with your AI companion
3. **Room Interaction**: Click objects in the room grid to interact with them
4. **Assistant Movement**: Click empty spaces to move your assistant
5. **Model Switching**: Use the model selector to switch between LLM providers

## Development Phases

See [DESKMATE_SPEC.md](DESKMATE_SPEC.md) for the complete development roadmap.

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic OpenAPI docs
- **WebSocket**: Real-time bidirectional communication for chat
- **SQLAlchemy**: Async ORM for PostgreSQL database operations
- **Qdrant**: Vector database for semantic memory storage
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern UI library with hooks and functional components
- **TypeScript**: Type-safe JavaScript for better development experience
- **Zustand**: Lightweight state management (chat, room, persona stores)
- **Tailwind CSS**: Utility-first CSS framework for responsive design

### LLM Integration
- **Ollama**: Local LLM hosting (llama3.2, phi-3, gemma, etc.)
- **Nano-GPT API**: Cloud-based LLM service integration
- **Streaming**: Real-time response streaming for better UX

### Development & Deployment
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving
- **Pytest**: Comprehensive test suite for backend
- **Hot Reload**: Development servers with automatic reloading

## Troubleshooting

### Common Issues

**WebSocket connection failed:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check Docker containers
docker compose ps
```

**Ollama model not found:**
```bash
# List available models
ollama list

# Pull a model
ollama pull llama3.2:latest
```

**Frontend build errors:**
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Contributing

This project uses conventional commits and automated co-authoring with Claude Code. All commits include proper attribution and follow semantic versioning principles.

## License

[License information to be added]