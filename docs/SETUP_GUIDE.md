# DeskMate Setup Guide

This guide will help you install and configure DeskMate on your system. Follow these steps to get your virtual AI companion up and running.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Methods](#installation-methods)
4. [Configuration](#configuration)
5. [First Launch](#first-launch)
6. [Troubleshooting Setup](#troubleshooting-setup)
7. [Advanced Configuration](#advanced-configuration)

## System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.15, or Ubuntu 18.04+
- **RAM**: 4GB (8GB recommended)
- **CPU**: Dual-core 2.0GHz (Quad-core recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for cloud AI models
- **Browser**: Chrome 90+, Firefox 85+, Safari 14+, or Edge 90+

### Recommended Setup
- **OS**: Latest versions of Windows 11, macOS 12+, or Ubuntu 20.04+
- **RAM**: 16GB for optimal performance
- **CPU**: Quad-core 3.0GHz+ for smooth operation
- **Storage**: 5GB free space for models and data
- **Network**: Stable broadband connection
- **Display**: Secondary monitor 1920x480 for kiosk mode

### For Local AI Models (Ollama)
- **RAM**: 8GB+ (16GB recommended for larger models)
- **CPU**: Modern multi-core processor
- **GPU**: Optional NVIDIA GPU for accelerated inference

## Prerequisites

### Required Software

#### 1. Docker and Docker Compose
**Docker** is required to run DeskMate services:

**Windows/Mac:**
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Install and start Docker Desktop
3. Verify installation: `docker --version` and `docker-compose --version`

**Linux (Ubuntu):**
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Restart to apply group changes
sudo systemctl restart docker
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

#### 2. Git (for source installation)
**Windows**: Download from [git-scm.com](https://git-scm.com/)
**Mac**: Install via Homebrew `brew install git` or Xcode Command Line Tools
**Linux**: `sudo apt install git`

#### 3. Web Browser
Ensure you have a modern browser:
- Chrome 90+ (recommended)
- Firefox 85+
- Safari 14+ (Mac only)
- Edge 90+

### Optional Software

#### Ollama (for local AI models)
If you want to run AI models locally:

1. Visit [ollama.ai](https://ollama.ai/)
2. Download and install for your operating system
3. Verify installation: `ollama --version`

#### Nano-GPT Account (for cloud AI)
For cloud-based AI models:

1. Visit [nano-gpt.com](https://nano-gpt.com/)
2. Create an account and get an API key
3. Note your API key for configuration

## Installation Methods

### Method 1: Quick Start with Docker (Recommended)

This is the fastest way to get DeskMate running:

```bash
# Clone the repository
git clone https://github.com/YourBr0ther/deskmate.git
cd deskmate

# Set up your API key (choose one method)
# Method A: Environment variable
export NANO_GPT_API_KEY="your_api_key_here"

# Method B: Create .env.local file
echo "NANO_GPT_API_KEY=your_api_key_here" > .env.local

# Method C: Edit backend/.env file
nano backend/.env  # Add your API key

# Start all services
docker-compose up -d

# Wait for services to start (about 2-3 minutes)
# Check status
docker-compose ps

# Open DeskMate
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Method 2: Development Setup

For developers or advanced users who want to modify DeskMate:

#### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys and settings

# Start databases with Docker
docker-compose up -d deskmate-postgres deskmate-qdrant

# Run backend
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup
```bash
# Navigate to frontend directory (new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Method 3: Production Deployment

For production servers or dedicated installations:

```bash
# Clone repository
git clone https://github.com/YourBr0ther/deskmate.git
cd deskmate

# Create production environment file
cp .env.example .env.production
nano .env.production  # Configure for production

# Build and start production services
docker-compose -f docker-compose.prod.yml up -d

# Set up reverse proxy (nginx example)
sudo nano /etc/nginx/sites-available/deskmate
# Configure nginx to proxy to localhost:3000

# Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/deskmate /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## Configuration

### Environment Variables

#### Required Configuration
Create a `.env.local` file in the root directory or set environment variables:

```bash
# AI Model Configuration
NANO_GPT_API_KEY=your_nano_gpt_api_key_here
NANO_GPT_BASE_URL=https://api.nanogpt.ai/v1

# Ollama Configuration (if using local models)
OLLAMA_BASE_URL=http://localhost:11434

# Default Settings
DEFAULT_LLM_MODEL=llama3.2:latest
LLM_MAX_TOKENS=2048
LLM_TIMEOUT=30

# Environment
ENVIRONMENT=production  # or development
DEBUG=false
LOG_LEVEL=INFO
```

#### Database Configuration (Advanced)
```bash
# PostgreSQL (handled by Docker Compose)
DATABASE_URL=postgresql://deskmate:deskmate@postgres:5432/deskmate

# Qdrant Vector Database
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # Optional, leave empty for local setup
```

### AI Model Setup

#### Option 1: Nano-GPT (Cloud)
1. Get API key from [nano-gpt.com](https://nano-gpt.com/)
2. Add to your environment configuration
3. No additional setup required

#### Option 2: Ollama (Local)
```bash
# Install Ollama first, then download models
ollama pull llama3.2:latest
ollama pull phi3:mini
ollama pull gemma-2b

# Verify models are available
ollama list

# Test model
ollama run llama3.2:latest "Hello, how are you?"
```

#### Option 3: Dual Setup (Recommended)
Configure both for maximum flexibility:
- Nano-GPT for complex reasoning and conversations
- Ollama for quick responses and idle mode

### Database Setup

Databases are automatically configured with Docker Compose, but you can customize:

#### PostgreSQL Configuration
```yaml
# In docker-compose.yml
postgres:
  environment:
    - POSTGRES_DB=deskmate
    - POSTGRES_USER=deskmate
    - POSTGRES_PASSWORD=your_secure_password
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

#### Qdrant Vector Database
```yaml
# In docker-compose.yml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
```

## First Launch

### Step-by-Step First Launch

1. **Start Services**
   ```bash
   docker-compose up -d
   ```

2. **Verify Services**
   ```bash
   # Check all containers are running
   docker-compose ps

   # Test backend health
   curl http://localhost:8000/health

   # Should return: {"status":"ok","timestamp":"..."}
   ```

3. **Access DeskMate**
   - Open browser to `http://localhost:3000`
   - Wait for interface to load (30-60 seconds first time)
   - Look for green connection indicator

4. **Test Basic Functionality**
   - Type "Hello!" in the chat box
   - Wait for response (may take 10-30 seconds first time)
   - Try clicking in the room grid to move your companion

5. **Configure Settings**
   - Click settings gear icon (⚙️)
   - Set your preferred AI model and persona
   - Adjust display and performance settings

### Initial Setup Checklist

- [ ] Docker containers are running (`docker-compose ps`)
- [ ] Backend health check passes (`curl localhost:8000/health`)
- [ ] Frontend loads without errors
- [ ] WebSocket connection established (green indicator)
- [ ] AI model responds to test message
- [ ] Room grid and companion are visible
- [ ] Settings panel opens and saves changes

## Troubleshooting Setup

### Common Setup Issues

#### Docker Problems

**Issue**: Docker not starting or permission errors
```bash
# Solution: Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Restart Docker service
sudo systemctl restart docker
```

**Issue**: Port conflicts (8000 or 3000 already in use)
```bash
# Solution: Check what's using the ports
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000

# Kill processes or change ports in docker-compose.yml
```

#### API Key Issues

**Issue**: Nano-GPT API key not working
1. Verify key is correct in your environment configuration
2. Check that key has sufficient credits/quota
3. Test key with curl:
   ```bash
   curl -H "Authorization: Bearer your_key_here" \
        https://api.nanogpt.ai/v1/models
   ```

**Issue**: Ollama not responding
```bash
# Check Ollama is running
ollama list

# Start Ollama service if needed
ollama serve

# Test model availability
ollama run llama3.2:latest "test"
```

#### Database Issues

**Issue**: Database connection failures
```bash
# Check database containers
docker-compose logs deskmate-postgres
docker-compose logs deskmate-qdrant

# Restart databases
docker-compose restart deskmate-postgres deskmate-qdrant

# Reset database volumes (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

#### Network Issues

**Issue**: Services can't communicate
```bash
# Check Docker network
docker network ls
docker network inspect deskmate_deskmate-network

# Restart Docker Compose
docker-compose down
docker-compose up -d
```

### Performance Issues

#### Slow Loading
- Increase Docker memory allocation (Docker Desktop settings)
- Ensure sufficient system RAM (8GB+ recommended)
- Check for background processes consuming resources

#### AI Model Performance
- Try lighter models (phi3:mini instead of llama3.2:latest)
- Increase timeout values in configuration
- Monitor system resources during AI inference

### Verification Commands

Run these to verify your setup:

```bash
# Service health checks
curl http://localhost:8000/health
curl http://localhost:8000/brain/test
curl http://localhost:3000

# Database connectivity
docker exec -it deskmate-postgres psql -U deskmate -d deskmate -c "SELECT version();"
curl http://localhost:6333/collections

# AI model tests
curl -X POST http://localhost:8000/chat/simple \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test message", "persona_name": "TestUser"}'
```

## Advanced Configuration

### Custom Personas

1. **Prepare Persona Files**
   - Use SillyTavern V2 format
   - PNG files with embedded JSON metadata
   - Place in `data/personas/` directory

2. **Load Custom Persona**
   ```bash
   # Copy persona file
   cp your_persona.png data/personas/

   # Restart services to detect new persona
   docker-compose restart deskmate-backend
   ```

### Performance Tuning

#### For High-Performance Systems
```bash
# In .env.local
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=60
DEFAULT_LLM_MODEL=llama3.2:latest
```

#### For Resource-Constrained Systems
```bash
# In .env.local
LLM_MAX_TOKENS=1024
LLM_TIMEOUT=30
DEFAULT_LLM_MODEL=phi3:mini
```

### Security Configuration

#### Production Security
```bash
# Use strong passwords
POSTGRES_PASSWORD=your_very_secure_password

# Restrict network access
# Bind to localhost only in docker-compose.yml
ports:
  - "127.0.0.1:8000:8000"
  - "127.0.0.1:3000:80"

# Use environment-specific configs
ENVIRONMENT=production
DEBUG=false
```

### Backup Configuration

#### Automated Backups
```bash
# Create backup script
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker exec deskmate-postgres pg_dump -U deskmate deskmate > backup_${DATE}.sql
tar -czf qdrant_backup_${DATE}.tar.gz -C /var/lib/docker/volumes/deskmate_qdrant_data/_data .
```

### Monitoring Setup

#### System Monitoring
```bash
# Install monitoring tools
docker run -d --name=monitoring \
  -p 3001:3000 \
  grafana/grafana

# Configure prometheus for metrics
# Add to docker-compose.yml
```

---

## Quick Setup Summary

For immediate setup:

```bash
# 1. Install Docker and Git
# 2. Clone repository
git clone https://github.com/YourBr0ther/deskmate.git
cd deskmate

# 3. Set API key
echo "NANO_GPT_API_KEY=your_key_here" > .env.local

# 4. Start services
docker-compose up -d

# 5. Wait 2-3 minutes, then open
# http://localhost:3000
```

If you encounter any issues, refer to the troubleshooting section above or check the [User Guide](USER_GUIDE.md) for detailed usage instructions.

---

*For ongoing usage and features, see the [User Guide](USER_GUIDE.md).*
*For technical details and development, see the [Developer Guide](DEVELOPER_GUIDE.md).*