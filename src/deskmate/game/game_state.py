"""Central game state manager."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from deskmate.core.config import Settings, get_personality, get_objects
from deskmate.domain.companion import Companion
from deskmate.domain.conversation import Conversation
from deskmate.domain.object import GameObject
from deskmate.domain.room import Room, WalkableArea
from deskmate.services.ollama_client import OllamaService

if TYPE_CHECKING:
    from deskmate.game.input_handler import GameAction


class ChatState(Enum):
    """State of the chat system."""

    IDLE = auto()
    WAITING_FOR_RESPONSE = auto()
    DISPLAYING_RESPONSE = auto()


@dataclass
class GameState:
    """Central game state container."""

    companion: Companion
    room: Room
    conversation: Conversation
    ollama_service: OllamaService | None
    settings: Settings
    chat_state: ChatState = ChatState.IDLE
    chat_input_active: bool = False
    chat_input_text: str = ""
    pending_speech_duration: float = 0.0

    @classmethod
    def from_settings(cls, settings: Settings) -> "GameState":
        """Create a GameState from settings."""
        # Create walkable area from config
        walkable_area = WalkableArea(
            min_x=settings.room.walkable_area.min_x,
            max_x=settings.room.walkable_area.max_x,
            min_y=settings.room.walkable_area.min_y,
            max_y=settings.room.walkable_area.max_y,
        )

        # Create room
        room = Room(
            name=settings.room.name,
            width=settings.display.width,
            height=settings.display.height,
            walkable_area=walkable_area,
        )

        # Load objects from config
        objects_config = get_objects()
        for obj_cfg in objects_config.objects:
            room.add_object(
                GameObject(
                    id=obj_cfg.id,
                    name=obj_cfg.name,
                    x=float(obj_cfg.x),
                    y=float(obj_cfg.y),
                    width=obj_cfg.width,
                    height=obj_cfg.height,
                    can_be_held=obj_cfg.can_be_held,
                    color=tuple(obj_cfg.color),  # type: ignore
                    shape=obj_cfg.shape,
                )
            )

        # Create companion at starting position
        companion = Companion(
            x=float(settings.companion.start_x),
            y=float(settings.companion.start_y),
        )

        # Create conversation
        conversation = Conversation(max_history=settings.chat.max_history)

        # Set up system prompt from personality
        personality = get_personality()
        system_prompt = cls._build_system_prompt(personality, room, companion)
        conversation.add_system_message(system_prompt)

        # Create Ollama service
        try:
            ollama_service = OllamaService(
                host=settings.ollama.host,
                model=settings.ollama.model,
                timeout=settings.ollama.timeout,
            )
        except Exception:
            # Ollama not available, continue without AI
            ollama_service = None

        return cls(
            companion=companion,
            room=room,
            conversation=conversation,
            ollama_service=ollama_service,
            settings=settings,
        )

    @staticmethod
    def _build_system_prompt(personality, room: Room, companion: Companion) -> str:
        """Build the system prompt from personality config."""
        p = personality.personality

        # Format traits
        traits_str = ", ".join(p.traits) if p.traits else "friendly"

        # Format speech style
        speech_style_str = "\n".join(f"- {s}" for s in p.speech_style) if p.speech_style else ""

        # Get holding status
        if companion.held_object:
            holding_status = f"holding a {companion.held_object.name}"
        else:
            holding_status = "not holding anything"

        # Get nearby objects
        nearby = room.get_nearby_objects(companion.x, companion.y, radius=200)
        nearby_names = [obj.name for obj in nearby if not obj.is_held]
        nearby_str = ", ".join(nearby_names) if nearby_names else "nothing nearby"

        # Use template if provided, otherwise use background
        if p.system_prompt_template:
            return p.system_prompt_template.format(
                name=p.name,
                background=p.background,
                traits=traits_str,
                speech_style=speech_style_str,
                room_name=room.name,
                holding_status=holding_status,
                nearby_objects=nearby_str,
            )
        else:
            return p.background

    def __init__(
        self,
        settings: Settings,
        companion: Companion | None = None,
        room: Room | None = None,
        conversation: Conversation | None = None,
        ollama_service: OllamaService | None = None,
        chat_state: ChatState = ChatState.IDLE,
        chat_input_active: bool = False,
        chat_input_text: str = "",
        pending_speech_duration: float = 0.0,
    ) -> None:
        """Initialize game state (prefer using from_settings class method)."""
        if companion is None or room is None or conversation is None:
            # Use from_settings to create a proper game state
            state = GameState.from_settings(settings)
            self.companion = state.companion
            self.room = state.room
            self.conversation = state.conversation
            self.ollama_service = state.ollama_service
        else:
            self.companion = companion
            self.room = room
            self.conversation = conversation
            self.ollama_service = ollama_service

        self.settings = settings
        self.chat_state = chat_state
        self.chat_input_active = chat_input_active
        self.chat_input_text = chat_input_text
        self.pending_speech_duration = pending_speech_duration

    def update(self, dt: float, actions: list["GameAction"]) -> None:
        """Update game state for one frame."""
        # Process actions
        for action in actions:
            self._process_action(action)

        # Update companion movement
        if self.companion.is_moving:
            self.companion.move_towards_target(
                self.settings.companion.move_speed, dt
            )
            # Clamp to walkable area
            clamped_x, clamped_y = self.room.clamp_to_walkable(
                self.companion.x, self.companion.y
            )
            self.companion.x = clamped_x
            self.companion.y = clamped_y

        # Poll for AI responses
        if self.ollama_service and self.chat_state == ChatState.WAITING_FOR_RESPONSE:
            response = self.ollama_service.poll_response()
            if response:
                if response["success"]:
                    content = response["content"]
                    self.conversation.add_assistant_message(content)
                    self.companion.say(content)
                    self.chat_state = ChatState.DISPLAYING_RESPONSE
                    # Show speech for ~3 seconds + 0.05s per character
                    self.pending_speech_duration = 3.0 + len(content) * 0.05
                else:
                    # Error occurred
                    error_msg = f"(AI unavailable: {response['error']})"
                    self.conversation.add_assistant_message(error_msg)
                    self.chat_state = ChatState.IDLE

        # Update speech bubble duration
        if self.chat_state == ChatState.DISPLAYING_RESPONSE:
            self.pending_speech_duration -= dt
            if self.pending_speech_duration <= 0:
                self.companion.stop_speaking()
                self.chat_state = ChatState.IDLE

    def _process_action(self, action: "GameAction") -> None:
        """Process a single game action."""
        from deskmate.game.input_handler import ActionType

        if action.action_type == ActionType.MOVE_TO:
            # Clamp target to walkable area
            target_x, target_y = self.room.clamp_to_walkable(action.x, action.y)
            self.companion.set_target(target_x, target_y)

        elif action.action_type == ActionType.CLICK_OBJECT:
            obj = self.room.get_object_at(action.x, action.y)
            if obj:
                self._handle_object_click(obj)

        elif action.action_type == ActionType.SEND_CHAT:
            self._send_chat_message(action.text)

        elif action.action_type == ActionType.TOGGLE_CHAT:
            self.chat_input_active = not self.chat_input_active

        elif action.action_type == ActionType.UPDATE_CHAT_INPUT:
            self.chat_input_text = action.text

        elif action.action_type == ActionType.DROP_OBJECT:
            self._drop_held_object()

    def _handle_object_click(self, obj: GameObject) -> None:
        """Handle clicking on an object."""
        # If companion is holding something, try to drop it first
        if self.companion.held_object:
            self._drop_held_object()
        else:
            # Try to pick up the object
            if self.companion.pickup(obj):
                # Move to object location
                self.companion.set_target(obj.x, obj.y)

    def _drop_held_object(self) -> None:
        """Drop the currently held object."""
        dropped = self.companion.drop()
        if dropped:
            # Make sure dropped object is in walkable area
            dropped.x, dropped.y = self.room.clamp_to_walkable(dropped.x, dropped.y)

    def _send_chat_message(self, text: str) -> None:
        """Send a chat message to the AI."""
        if not text.strip():
            return

        # Add user message
        self.conversation.add_user_message(text)

        # Send to Ollama if available
        if self.ollama_service:
            self.ollama_service.send_message(
                messages=self.conversation.to_ollama_messages(),
                request_id=f"msg-{len(self.conversation.messages)}",
            )
            self.chat_state = ChatState.WAITING_FOR_RESPONSE
        else:
            # No AI available, show a placeholder response
            self.conversation.add_assistant_message(
                "*looks confused* (AI not connected - check Ollama)"
            )

        self.chat_input_text = ""

    def shutdown(self) -> None:
        """Clean up resources."""
        if self.ollama_service:
            self.ollama_service.shutdown()
