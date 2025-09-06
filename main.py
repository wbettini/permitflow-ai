from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from core.state_manager import StateManager
from agents.flowbot.flowbot import FlowBot

app = FastAPI(title="PermitFlow-AI", version="0.2.0")

# -------------------------
# WebSocket: FlowBot Live Chat
# -------------------------
@app.websocket("/ws/flowbot")
async def websocket_flowbot(websocket: WebSocket):
    await websocket.accept()

    # Initialise new FlowBot
    required_fields = ["service_name", "owner", "data_classification"]
    state = StateManager()
    bot = FlowBot(state, required_fields, prompts_file="permitFlowDb/tollgate_prompts.json")

    await websocket.send_text("👋 Hi, I'm FlowBot! What type of 'Permit to...' are we working on today?")

    try:
        while True:
            data = await websocket.receive_text()

            # First message = permit type
            if not state.get("permit_type"):
                if not data.lower().startswith("permit to"):
                    await websocket.send_text(
                        "Which type of permit are we working on? For example: Permit to Design, Permit to Build, Permit to Operate."
                    )
                    continue
                start_msg = bot.start(data)
                await websocket.send_text(start_msg)
                continue

            # All subsequent messages go through FlowBot's natural-language aware converse()
            reply = bot.converse(data)
            await websocket.send_text(reply)

            # Optional: detect end of process
            if bot.current_tollgate == 3 and "Process complete" in reply:
                break

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(f"⚠️ Error: {e}")

# -------------------------
# Serve Chat UI + Static Assets
# -------------------------

@app.get("/")
async def root():
    return FileResponse(os.path.join("public", "index.html"))

app.mount("/static", StaticFiles(directory="public"), name="static")

# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}