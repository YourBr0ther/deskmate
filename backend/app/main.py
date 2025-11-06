import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, personas, room, assistant, chat, websocket, conversation, brain_council, room_navigation, frontend
from app.config import config
from app.db.database import init_db
from app.middleware import RateLimitMiddleware, ErrorHandlerMiddleware
from app.logging_config import init_logging, PerformanceLogger

# Initialize enhanced logging first
init_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeskMate backend...", extra={
        "operation": "startup",
        "service": "deskmate-backend",
        "version": config.version
    })

    with PerformanceLogger("database_initialization"):
        await init_db()

    # Start idle controller for autonomous behavior
    from app.services.idle_controller import idle_controller
    with PerformanceLogger("idle_controller_startup"):
        await idle_controller.start()
    logger.info("Idle controller started", extra={"operation": "idle_controller_started"})

    logger.info("DeskMate backend startup completed successfully", extra={
        "operation": "startup_complete",
        "service": "deskmate-backend"
    })

    yield

    # Shutdown sequence
    logger.info("Shutting down DeskMate backend...", extra={"operation": "shutdown"})

    with PerformanceLogger("idle_controller_shutdown"):
        await idle_controller.stop()
    logger.info("Idle controller stopped", extra={"operation": "idle_controller_stopped"})

    logger.info("DeskMate backend shutdown completed", extra={"operation": "shutdown_complete"})


app = FastAPI(
    title=config.title,
    description=config.description,
    version=config.version,
    lifespan=lifespan
)

# Add middleware (order matters - error handling first, then rate limiting, then CORS)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS settings from configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(personas.router)
app.include_router(room.router)
app.include_router(assistant.router)
app.include_router(chat.router)
app.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
app.include_router(brain_council.router)
app.include_router(room_navigation.router)
app.include_router(frontend.router)
app.include_router(websocket.router)