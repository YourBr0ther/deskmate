# DeskMate v2 - Pygame Edition

A virtual AI companion for your desktop, built with Pygame and Ollama.

## Features

- **Interactive Companion**: A pixel-art style companion that lives on your desktop
- **AI-Powered Chat**: Conversational AI using Ollama (supports any model)
- **Object Interaction**: Pick up, hold, and drop objects in the room
- **Configurable Personality**: Customize your companion's personality via YAML

## Requirements

- Python 3.11+
- Ollama running locally (optional, for AI chat)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:YourBr0ther/DeskMate.git
cd DeskMate
git checkout v2-pygame-mvp
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

3. (Optional) Start Ollama with your preferred model:
```bash
ollama run llama3.2
```

## Running

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m deskmate
```

## Controls

- **Left Click**: Move companion to location / Interact with objects
- **Right Click**: Drop held object
- **T or Enter**: Open chat input
- **Escape**: Cancel chat input
- **D**: Drop held object

## Configuration

### Settings (`config/settings.yaml`)

Configure display, companion behavior, and Ollama connection:

```yaml
display:
  width: 1024
  height: 768
  fps: 60

ollama:
  host: "http://localhost:11434"
  model: "llama3.2"  # Change to your preferred model
```

### Personality (`config/personality.yaml`)

Customize your companion's personality:

```yaml
personality:
  name: "Pixel"
  traits:
    - friendly
    - curious
    - playful
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Architecture

The project follows a clean layered architecture:

```
src/deskmate/
├── core/          # Configuration, events, assets
├── domain/        # Pure Python domain models (no Pygame)
├── services/      # External services (Ollama)
├── game/          # Game state and logic
└── rendering/     # Pygame rendering (sprites, UI)
```

Key principle: Domain and game logic have no Pygame dependency, making them fully testable.

## License

MIT
