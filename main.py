from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from core.orchestration import Orchestrator
import os

app = FastAPI(title="PermitFlow-AI", version="0.2.0")

# -------------------------
# WebSocket: FlowBot Live Chat
# -------------------------
@app.websocket("/ws/flowbot")
async def websocket_flowbot(websocket: WebSocket):
    await websocket.accept()
    orch = Orchestrator()
    await websocket.send_text("👋 Hi, I'm FlowBot! What type of permit are we working on today?")

    try:
        while True:
            data = await websocket.receive_text()

            # First message = permit type
            if not orch.state.get("permit_type"):
                start_msg = orch.start_permit(data)
                if "error" in start_msg:
                    await websocket.send_text(start_msg["error"])
                    continue
                await websocket.send_text(start_msg["message"])
                await websocket.send_text("Please provide the first piece of application info (key=value).")
                continue

            # Subsequent messages = application data
            if "=" in data:
                key, value = data.split("=", 1)
                step = orch.continue_permit({key.strip(): value.strip()})
            else:
                await websocket.send_text("⚠️ Please send data as key=value")
                continue

            if step.get("status") == "incomplete":
                await websocket.send_text(step["message"])
            elif step.get("status") == "finished":
                await websocket.send_text("✅ All steps complete! Here's the result:")
                await websocket.send_json(step)
                break
            else:
                await websocket.send_text(step.get("message", "OK"))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(f"⚠️ Error: {e}")

# -------------------------
# Serve Chat UI + Static Assets
# -------------------------

# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse(os.path.join("public", "index.html"))

# Serve /static/* for CSS/JS/images
app.mount("/static", StaticFiles(directory="public"), name="static")

# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}