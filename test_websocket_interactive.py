#!/usr/bin/env python3
"""
Interactive WebSocket test for Brain Council.
Shows real-time responses and actions.
"""

import asyncio
import json
import websockets
import sys


async def interactive_test():
    """Interactive WebSocket test with better timeout handling."""
    uri = "ws://localhost:8000/ws"

    print("🔌 Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        print("✅ Connected! Waiting for initial state...")

        # Get initial messages
        for _ in range(2):
            msg = await websocket.recv()
            data = json.loads(msg)
            if data['type'] == 'assistant_state':
                pos = data['data']['position']
                print(f"🤖 Assistant at: ({pos['x']}, {pos['y']})")
            elif data['type'] == 'connection_established':
                print(f"✅ Connected with {data['data']['provider']}")

        # Test messages
        test_cases = [
            "Hello, how are you?",
            "Can you move to the desk?",
            "What objects are near you?",
            "Turn on the lamp please"
        ]

        for test_msg in test_cases:
            print(f"\n📤 Sending: {test_msg}")
            await websocket.send(json.dumps({
                "type": "chat_message",
                "data": {
                    "message": test_msg,
                    "persona_context": {
                        "name": "Test Assistant",
                        "personality": "Helpful and friendly"
                    }
                }
            }))

            # Collect response for up to 5 seconds
            response_text = ""
            deadline = asyncio.get_event_loop().time() + 5

            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(msg)

                    if data['type'] == 'chat_stream':
                        response_text += data['data']['content']
                        print(data['data']['content'], end='', flush=True)
                    elif data['type'] == 'assistant_state':
                        pos = data['data']['position']
                        print(f"\n🚶 Moved to: ({pos['x']}, {pos['y']})")
                    elif data['type'] == 'assistant_typing':
                        if data['data']['typing']:
                            print("💭 Thinking...", end='', flush=True)
                    elif data['type'] == 'room_update':
                        print(f"\n🔧 Room updated: {data['data']}")

                except asyncio.TimeoutError:
                    if response_text:
                        break

            print()  # New line after response
            await asyncio.sleep(1)  # Pause between tests

        print("\n✅ All tests completed!")


if __name__ == "__main__":
    print("🧪 Brain Council WebSocket Interactive Test")
    print("=" * 50)
    asyncio.run(interactive_test())