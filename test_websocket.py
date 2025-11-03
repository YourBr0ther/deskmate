#!/usr/bin/env python3
"""
Test WebSocket chat connection to debug the "I don't know how to help with that" issue.
"""
import asyncio
import websockets
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
backend_path = Path(__file__).parent / "backend"
env_path = backend_path / ".env"
load_dotenv(env_path)

async def test_websocket_chat():
    """Test WebSocket chat functionality."""
    uri = "ws://localhost:8000/ws"

    try:
        print("🔗 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Send a test message
            test_message = {
                "type": "chat_message",
                "data": {
                    "message": "Hello! Can you help me test this chat system?",
                    "persona_context": None
                }
            }

            print(f"📤 Sending message: {test_message['data']['message']}")
            await websocket.send(json.dumps(test_message))

            # Listen for responses
            print("👂 Listening for responses...")
            response_count = 0
            full_response = ""

            while response_count < 10:  # Listen for up to 10 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    response_count += 1

                    print(f"📥 Response {response_count}: {data}")

                    if data.get("type") == "chat_stream":
                        content = data.get("data", {}).get("content", "")
                        full_response += content
                        print(f"   Stream chunk: '{content}'")
                    elif data.get("type") == "assistant_typing":
                        typing = data.get("data", {}).get("typing", False)
                        print(f"   Typing indicator: {typing}")
                    elif data.get("type") == "error":
                        error_msg = data.get("data", {}).get("message", "Unknown error")
                        print(f"❌ Error: {error_msg}")
                        break

                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break

            print(f"\n📝 Full response: '{full_response.strip()}'")

            if "I'm not sure how to respond" in full_response or "trouble processing" in full_response:
                print("❌ Got fallback response - Brain Council might be failing")
                return False
            elif full_response.strip():
                print("✅ Got proper response from Brain Council!")
                return True
            else:
                print("⚠️  No response content received")
                return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 Testing WebSocket Chat")
    print("=" * 40)

    success = await test_websocket_chat()

    if success:
        print("\n🎉 WebSocket chat test passed!")
    else:
        print("\n❌ WebSocket chat test failed")
        print("💡 Check backend logs with: docker compose logs backend --tail=50")

if __name__ == "__main__":
    asyncio.run(main())