import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, personas, room, assistant, chat, websocket, conversation, brain_council, room_navigation, frontend
from app.config import config
from app.db.database import init_db
from app.middleware import RateLimitMiddleware

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeskMate backend...")
    await init_db()

    # Start idle controller for autonomous behavior
    from app.services.idle_controller import idle_controller
    await idle_controller.start()
    logger.info("Idle controller started")

    yield

    # Stop idle controller
    await idle_controller.stop()
    logger.info("Idle controller stopped")
    logger.info("Shutting down DeskMate backend...")


app = FastAPI(
    title=config.title,
    description=config.description,
    version=config.version,
    lifespan=lifespan
)

# Add middleware (order matters - rate limiting first, then CORS)
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