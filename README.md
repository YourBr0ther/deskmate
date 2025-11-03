# DeskMate - Virtual AI Companion

DeskMate is a virtual AI companion that lives in a simulated room environment displayed on a secondary 1920x480 monitor. The companion uses LLM technology and persona cards (SillyTavern-compatible) to create an interactive, living desktop assistant.

## Project Status

**Current Phase**: Phase 1 - Foundation & Infrastructure (Complete)
- ✅ Project structure created
- ✅ Docker Compose configuration
- ✅ Basic FastAPI backend with health check
- ✅ Qdrant vector database integration
- ✅ PostgreSQL database setup
- ✅ Health check tests

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development - coming in Phase 2)
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

- **Backend**: FastAPI (Python 3.11+)
- **Vector Database**: Qdrant
- **Relational Database**: PostgreSQL
- **Frontend**: React + Electron (coming in Phase 2)

## API Documentation

Once running, visit:
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

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