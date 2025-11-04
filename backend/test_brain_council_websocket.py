#!/usr/bin/env python3
"""
Test script for Brain Council WebSocket integration.
"""

import asyncio
import json
import websockets
import sys


async def test_brain_council_websocket():
    """Test WebSocket connection and Brain Council processing."""
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")

            # Wait for initial connection message
            initial = await websocket.recv()
            print(f"📨 Initial message: {json.loads(initial)['type']}")

            # Send a test message through Brain Council
            test_message = {
                "type": "chat_message",
                "data": {
                    "message": "Hello! Can you move to position 20, 10?",
                    "persona_context": {
                        "name": "Test Assistant",
                        "personality": "Friendly and helpful"
                    }
                }
            }

            print(f"📤 Sending test message: {test_message['data']['message']}")
            await websocket.send(json.dumps(test_message))

            # Receive responses
            response_count = 0
            max_responses = 10

            while response_count < max_responses:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)

                    if data['type'] == 'chat_stream':
                        print(f"💬 Stream: {data['data']['content']}", end='')
                    elif data['type'] == 'assistant_state':
                        pos = data['data']['position']
                        print(f"\n🤖 Assistant moved to: ({pos['x']}, {pos['y']})")
                    elif data['type'] == 'assistant_typing':
                        typing = data['data']['typing']
                        print(f"\n⌨️  Typing: {typing}")
                    elif data['type'] == 'error':
                        print(f"\n❌ Error: {data['data']['message']}")
                        break
                    else:
                        print(f"\n📩 {data['type']}: {data.get('data', {})}")

                    response_count += 1

                except asyncio.TimeoutError:
                    print("\n⏱️  Timeout - no more messages")
                    break

            print("\n✅ Test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🧪 Testing Brain Council WebSocket Integration")
    print("=" * 50)

    success = await test_brain_council_websocket()

    print("=" * 50)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())