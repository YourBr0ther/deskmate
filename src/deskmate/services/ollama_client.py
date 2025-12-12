"""Thread-safe Ollama client for AI communication."""

import queue
import threading
import uuid
from dataclasses import dataclass
from typing import Any

from ollama import Client


@dataclass
class OllamaRequest:
    """A request to send to Ollama."""

    id: str
    messages: list[dict[str, str]]


@dataclass
class OllamaResponse:
    """A response from Ollama."""

    request_id: str
    success: bool
    content: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "content": self.content,
            "error": self.error,
        }


class OllamaService:
    """
    Thread-safe Ollama API wrapper.

    Uses a background worker thread to handle API calls,
    allowing the main game loop to remain responsive.
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: int = 30,
    ) -> None:
        """
        Initialize the Ollama service.

        Args:
            host: Ollama API host URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.host = host
        self.model = model
        self.timeout = timeout

        # Create client
        self.client = Client(host=host, timeout=timeout)

        # Communication queues
        self.request_queue: queue.Queue[OllamaRequest | None] = queue.Queue()
        self.response_queue: queue.Queue[OllamaResponse] = queue.Queue()

        # Start worker thread
        self._shutdown = False
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _worker_loop(self) -> None:
        """Background worker that processes Ollama requests."""
        while not self._shutdown:
            try:
                # Wait for request with timeout to allow shutdown checks
                try:
                    request = self.request_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if request is None:
                    # Shutdown signal
                    break

                # Process the request
                try:
                    response = self.client.chat(
                        model=self.model,
                        messages=request.messages,
                    )

                    self.response_queue.put(
                        OllamaResponse(
                            request_id=request.id,
                            success=True,
                            content=response["message"]["content"],
                        )
                    )

                except Exception as e:
                    self.response_queue.put(
                        OllamaResponse(
                            request_id=request.id,
                            success=False,
                            error=str(e),
                        )
                    )

            except Exception:
                # Unexpected error, continue running
                pass

    def send_message(
        self,
        messages: list[dict[str, str]],
        request_id: str | None = None,
    ) -> str:
        """
        Queue a message to send to Ollama.

        Args:
            messages: List of messages in Ollama format
            request_id: Optional request ID for tracking

        Returns:
            The request ID
        """
        if request_id is None:
            request_id = str(uuid.uuid4())

        request = OllamaRequest(id=request_id, messages=messages)
        self.request_queue.put(request)
        return request_id

    def poll_response(self) -> dict[str, Any] | None:
        """
        Non-blocking check for responses.

        Returns:
            Response dict if available, None otherwise
        """
        try:
            response = self.response_queue.get_nowait()
            return response.to_dict()
        except queue.Empty:
            return None

    def shutdown(self) -> None:
        """Shut down the worker thread."""
        self._shutdown = True
        self.request_queue.put(None)  # Signal worker to stop
        self._worker.join(timeout=2.0)

    def is_available(self) -> bool:
        """
        Check if Ollama is available.

        Returns:
            True if Ollama is reachable
        """
        try:
            self.client.list()
            return True
        except Exception:
            return False
