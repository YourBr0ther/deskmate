#!/usr/bin/env python3
"""
Simple WebSocket test script for DeskMate chat.
"""

import asyncio
import websockets
import json


async def test_websocket():
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")

            # Listen for initial messages
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"Initial message: {initial_message}")

                # Parse and check for connection established
                data = json.loads(initial_message)
                if data.get("type") == "assistant_state":
                    print("Received assistant state")

                # Wait for connection established message
                connection_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"Connection message: {connection_message}")

            except asyncio.TimeoutError:
                print("No initial messages received")

            # Send a chat message
            chat_message = {
                "type": "chat_message",
                "data": {
                    "message": "Hello from WebSocket! Can you tell me a short joke?"
                }
            }

            await websocket.send(json.dumps(chat_message))
            print("Sent chat message")

            # Listen for responses
            response_count = 0
            full_response = ""

            while response_count < 20:  # Limit responses to avoid infinite loop
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15)
                    data = json.loads(message)

                    print(f"Received: {data['type']}")

                    if data["type"] == "chat_stream":
                        chunk = data["data"]["content"]
                        full_response += chunk
                        print(f"Chunk: '{chunk}'")

                    elif data["type"] == "chat_message":
                        if data["data"]["role"] == "assistant":
                            print(f"Final assistant response: {data['data']['content']}")
                            break

                    elif data["type"] == "assistant_typing":
                        typing = data["data"]["typing"]
                        print(f"Assistant typing: {typing}")

                    response_count += 1

                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    break

            print(f"Full streamed response: '{full_response}'")

    except Exception as e:
        print(f"WebSocket connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())