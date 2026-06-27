import asyncio
import websockets
import json

# We connect as 'test_user_alpha' to match our Fusion Engine test
WEBSOCKET_URL = "ws://localhost:8000/api/v1/sensors/ws/test_user_alpha"

async def listen_for_alerts():
    print(f"📱 Connecting phone to server: {WEBSOCKET_URL}")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ Connected! Phone is locked and listening quietly in the background...\n")
            
            while True:
                # Wait for the backend to push a message down the pipe
                message = await websocket.recv()
                payload = json.loads(message)
                
                print("🚨 WAKE UP! MESSAGE RECEIVED FROM SERVER 🚨")
                print(json.dumps(payload, indent=2))
                
                if payload.get("type") == "CRITICAL_ESCALATION_WARNING":
                    print("\n>> POPPING 10-SECOND CANCELLATION WINDOW ON SCREEN <<\n")

    except Exception as e:
        print(f"Connection closed or failed: {e}")

if __name__ == "__main__":
    asyncio.run(listen_for_alerts())