"""
Load testing suite for DeskMate using Locust.
Tests API endpoints, WebSocket connections, and concurrent user scenarios.

To run: locust -f locustfile.py --host=http://localhost:8000
"""

import json
import random
import time
from locust import HttpUser, TaskSet, task, between
from locust.contrib.fasthttp import FastHttpUser
import websocket
import threading
import uuid


class DeskMateAPITaskSet(TaskSet):
    """Task set for testing DeskMate API endpoints."""

    def on_start(self):
        """Initialize test data."""
        self.persona_name = f"TestUser_{random.randint(1000, 9999)}"
        self.assistant_id = "test_assistant"

        # Test data
        self.sample_messages = [
            "Hello, how are you?",
            "Move to position 20, 10",
            "Turn on the lamp",
            "What can you see in the room?",
            "Sit on the bed",
            "What objects are nearby?",
            "I want to relax",
            "Turn off the lamp",
            "Move to the window",
            "How are you feeling?"
        ]

        self.sample_positions = [
            {"x": 10, "y": 5},
            {"x": 20, "y": 8},
            {"x": 30, "y": 12},
            {"x": 15, "y": 3},
            {"x": 45, "y": 10}
        ]

    @task(10)
    def health_check(self):
        """Test health endpoint - most frequent."""
        self.client.get("/health")

    @task(8)
    def get_assistant_state(self):
        """Test getting assistant state."""
        self.client.get("/assistant")

    @task(6)
    def brain_council_test(self):
        """Test Brain Council endpoint."""
        self.client.get("/brain/test")

    @task(5)
    def chat_simple(self):
        """Test simple chat endpoint."""
        message = random.choice(self.sample_messages)
        response = self.client.post("/chat/simple", json={
            "message": message,
            "persona_name": self.persona_name
        })

    @task(4)
    def brain_process_message(self):
        """Test Brain Council message processing."""
        message = random.choice(self.sample_messages)
        self.client.post("/brain/process", json={
            "message": message,
            "persona_context": {
                "name": self.persona_name,
                "personality": "Friendly test persona"
            }
        })

    @task(3)
    def move_assistant(self):
        """Test assistant movement."""
        position = random.choice(self.sample_positions)
        self.client.post("/assistant/move", json=position)

    @task(3)
    def brain_analyze(self):
        """Test Brain Council analysis."""
        self.client.post("/brain/analyze", json={
            "include_memory": True,
            "persona_name": self.persona_name
        })

    @task(2)
    def get_chat_models(self):
        """Test getting available models."""
        self.client.get("/chat/models")

    @task(2)
    def memory_stats(self):
        """Test memory statistics."""
        self.client.get("/conversation/memory/stats")

    @task(1)
    def clear_memory(self):
        """Test memory clearing (infrequent)."""
        self.client.post("/conversation/memory/clear")

    @task(1)
    def get_conversation_history(self):
        """Test conversation history retrieval."""
        self.client.get("/conversation/history")


class WebSocketTaskSet(TaskSet):
    """Task set for testing WebSocket connections."""

    def on_start(self):
        """Initialize WebSocket connection."""
        self.ws = None
        self.connected = False
        self.message_count = 0
        self.response_times = []

        self.persona_name = f"WSUser_{random.randint(1000, 9999)}"

        # Connect to WebSocket
        self.connect_websocket()

    def connect_websocket(self):
        """Establish WebSocket connection."""
        try:
            ws_url = f"ws://localhost:8000/ws"
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_ws_open,
                on_message=self.on_ws_message,
                on_error=self.on_ws_error,
                on_close=self.on_ws_close
            )

            # Start WebSocket in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()

            # Wait for connection
            time.sleep(2)

        except Exception as e:
            print(f"WebSocket connection failed: {e}")

    def on_ws_open(self, ws):
        """WebSocket connection opened."""
        self.connected = True
        print(f"WebSocket connected for {self.persona_name}")

    def on_ws_message(self, ws, message):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            self.message_count += 1

            # Record response time if this was a response to our message
            if data.get("type") in ["chat_response", "assistant_moved", "status_update"]:
                response_time = time.time() - getattr(self, 'last_send_time', time.time())
                self.response_times.append(response_time)

        except json.JSONDecodeError:
            pass

    def on_ws_error(self, ws, error):
        """Handle WebSocket error."""
        print(f"WebSocket error: {error}")
        self.connected = False

    def on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        self.connected = False
        print(f"WebSocket closed for {self.persona_name}")

    @task(10)
    def send_chat_message(self):
        """Send chat message via WebSocket."""
        if not self.connected or not self.ws:
            return

        messages = [
            "Hello via WebSocket!",
            "How are you doing?",
            "Tell me about the room",
            "I want to move around",
            "What can you do?"
        ]

        message = {
            "type": "chat",
            "content": random.choice(messages),
            "persona_name": self.persona_name
        }

        self.last_send_time = time.time()
        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            print(f"Failed to send WebSocket message: {e}")

    @task(5)
    def send_assistant_move(self):
        """Send assistant movement via WebSocket."""
        if not self.connected or not self.ws:
            return

        move_message = {
            "type": "assistant_move",
            "x": random.randint(5, 59),
            "y": random.randint(2, 14)
        }

        self.last_send_time = time.time()
        try:
            self.ws.send(json.dumps(move_message))
        except Exception as e:
            print(f"Failed to send move command: {e}")

    @task(3)
    def request_status(self):
        """Request status via WebSocket."""
        if not self.connected or not self.ws:
            return

        status_message = {
            "type": "status_request"
        }

        self.last_send_time = time.time()
        try:
            self.ws.send(json.dumps(status_message))
        except Exception as e:
            print(f"Failed to request status: {e}")

    def on_stop(self):
        """Clean up WebSocket connection."""
        if self.ws:
            self.ws.close()

        # Print statistics
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            print(f"WebSocket user {self.persona_name} stats:")
            print(f"  Messages sent/received: {self.message_count}")
            print(f"  Average response time: {avg_response_time:.2f}s")


class DeskMateAPIUser(FastHttpUser):
    """HTTP API load testing user."""
    tasks = [DeskMateAPITaskSet]
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    weight = 3  # Higher weight for API testing


class DeskMateWebSocketUser(HttpUser):
    """WebSocket load testing user."""
    tasks = [WebSocketTaskSet]
    wait_time = between(2, 5)  # Wait 2-5 seconds between WebSocket messages
    weight = 1  # Lower weight for WebSocket testing


class HeavyLoadTaskSet(TaskSet):
    """Heavy load testing scenarios."""

    def on_start(self):
        """Initialize heavy load test."""
        self.persona_name = f"HeavyUser_{random.randint(1000, 9999)}"
        self.session_id = str(uuid.uuid4())

    @task(1)
    def complex_brain_council_session(self):
        """Simulate complex Brain Council session."""
        complex_messages = [
            "I want to turn on the lamp, then move to the bed, and finally sit down while you tell me a story about the room",
            "Analyze the current room state, suggest three different activities I could do, and explain the reasoning behind each suggestion",
            "Move around the room in a pattern that visits each object, interact with each one appropriately, and describe what you're doing at each step",
            "I'm feeling confused about my surroundings. Can you help me understand where everything is located and how I can interact with the environment?",
            "Demonstrate your spatial reasoning by describing the room from different perspectives and planning the most efficient path to complete multiple tasks"
        ]

        message = random.choice(complex_messages)

        # Time the complex request
        start_time = time.time()

        response = self.client.post("/brain/process", json={
            "message": message,
            "persona_context": {
                "name": self.persona_name,
                "personality": "Analytical and detail-oriented test persona",
                "session_id": self.session_id
            }
        })

        processing_time = time.time() - start_time

        # Log slow responses
        if processing_time > 5.0:
            print(f"Slow Brain Council response: {processing_time:.2f}s for user {self.persona_name}")

    @task(1)
    def rapid_fire_commands(self):
        """Send rapid commands to test system resilience."""
        commands = [
            {"endpoint": "/assistant/move", "data": {"x": random.randint(0, 63), "y": random.randint(0, 15)}},
            {"endpoint": "/brain/analyze", "data": {"persona_name": self.persona_name}},
            {"endpoint": "/conversation/memory/stats", "data": {}},
            {"endpoint": "/assistant", "data": {}}
        ]

        # Send 5 rapid requests
        for _ in range(5):
            cmd = random.choice(commands)
            if cmd["data"]:
                self.client.post(cmd["endpoint"], json=cmd["data"])
            else:
                self.client.get(cmd["endpoint"])
            time.sleep(0.1)  # Very short delay


class HeavyLoadUser(FastHttpUser):
    """Heavy load testing user for stress testing."""
    tasks = [HeavyLoadTaskSet]
    wait_time = between(0.5, 1.5)  # Aggressive timing
    weight = 1  # Low weight, only for stress testing


# Test scenarios for different load types
class LightLoadUser(FastHttpUser):
    """Light load user simulating casual usage."""
    tasks = [DeskMateAPITaskSet]
    wait_time = between(5, 15)  # Casual user timing
    weight = 2

    @task(15)
    def casual_browsing(self):
        """Simulate casual browsing behavior."""
        endpoints = ["/health", "/assistant", "/conversation/memory/stats"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)

    @task(5)
    def occasional_chat(self):
        """Send occasional chat messages."""
        simple_messages = ["Hi", "How are you?", "What's up?"]
        message = random.choice(simple_messages)
        self.client.post("/chat/simple", json={
            "message": message,
            "persona_name": "CasualUser"
        })


# Custom test scenarios
def create_burst_load_test():
    """Create a burst load test scenario."""

    class BurstTaskSet(TaskSet):
        @task(1)
        def burst_requests(self):
            """Send burst of requests."""
            for _ in range(10):
                self.client.get("/health")
                self.client.get("/assistant")

    class BurstUser(FastHttpUser):
        tasks = [BurstTaskSet]
        wait_time = between(10, 20)  # Long wait, then burst

    return BurstUser


def create_memory_stress_test():
    """Create memory stress test scenario."""

    class MemoryStressTaskSet(TaskSet):
        @task(1)
        def memory_intensive_operations(self):
            """Perform memory-intensive operations."""
            # Send large messages
            large_message = "This is a large message. " * 100
            self.client.post("/chat/simple", json={
                "message": large_message,
                "persona_name": f"MemoryUser_{random.randint(1000, 9999)}"
            })

            # Request memory stats
            self.client.get("/conversation/memory/stats")

            # Analyze with memory
            self.client.post("/brain/analyze", json={
                "include_memory": True,
                "persona_name": "MemoryUser"
            })

    class MemoryStressUser(FastHttpUser):
        tasks = [MemoryStressTaskSet]
        wait_time = between(1, 3)

    return MemoryStressUser


# Performance monitoring functions
def log_performance_metrics():
    """Log performance metrics during load testing."""
    import psutil
    import threading

    def monitor():
        while True:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            print(f"System metrics - CPU: {cpu_percent}%, Memory: {memory.percent}%")
            time.sleep(10)

    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.daemon = True
    monitor_thread.start()


# Main execution for standalone testing
if __name__ == "__main__":
    print("DeskMate Load Testing Suite")
    print("Available user types:")
    print("- DeskMateAPIUser: HTTP API testing")
    print("- DeskMateWebSocketUser: WebSocket testing")
    print("- HeavyLoadUser: Stress testing")
    print("- LightLoadUser: Casual usage simulation")
    print("\nTo run: locust -f locustfile.py --host=http://localhost:8000")

    # Start performance monitoring
    log_performance_metrics()