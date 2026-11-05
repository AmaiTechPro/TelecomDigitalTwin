import asyncio
import websockets


async def test_connection():

    uri = "ws://127.0.0.1:8000/ws/telemetry"

    print("Connecting to WebSocket server...")

    try:
        async with websockets.connect(uri) as websocket:

            print("WebSocket connection successful!")
            print("Connected to:", uri)

            await websocket.send("Hello from Telecom Digital Twin!")

            print("Test message sent.")

    except Exception as error:
        print("WebSocket connection failed:", error)


asyncio.run(test_connection())