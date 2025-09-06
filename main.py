from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from core.site_properties import get_site_property
import os

from core.state_manager import StateManager
from agents.flowbot.flowbot import FlowBot
from core.site_properties import get_site_property


# -------------------------
# FastAPI App Initialization
# -------------------------
app = FastAPI(title="PermitFlow-AI", version="0.2.0")
print("🚀 FlowBot is live and listening...")

# -------------------------
# WebSocket: FlowBot Live Chat
# -------------------------
@app.websocket("/ws/flowbot")
async def websocket_flowbot(websocket: WebSocket):
    await websocket.accept()

    # Initialise new FlowBot
    bot_name = get_site_property("FLOWBOT_PREFERRED_NAME", "FlowBot")
    required_fields = ["service_name", "owner", "data_classification"]
    state = StateManager()
    bot = FlowBot(state, required_fields, prompts_file="permitFlowDb/tollgate_prompts.json")

    await websocket.send_text(f"👋 Hi, I'm {bot_name}! What type of 'Permit to...' are we working on today?")

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
        print(f"⚠️ WebSocket error: {e}")
        await websocket.send_text(f"⚠️ Error: {e}")

# -------------------------
# Serve Chat UI + Static Assets
# -------------------------
@app.get("/")
async def root():
    index_path = os.path.join("public", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content={"message": "UI not found"}, status_code=404)

app.mount("/static", StaticFiles(directory="public"), name="static")

# -------------------------
# Health Check
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Version Endpoint
# -------------------------
@app.get("/version")
def version():
    return {
        "app_name": app.title,
        "version": app.version,
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "port": os.environ.get("PORT", "8000")
    }

# -------------------------
# get_site_property
# -------------------------
@app.get("/site-properties")
def site_properties():
    return {
        "FLOWBOT_PREFERRED_NAME": get_site_property("FLOWBOT_PREFERRED_NAME", "FlowBot"),
        "SUPPORT_EMAIL": get_site_property("SUPPORT_EMAIL", "support@permitflow.bettini.us"),
        "DEFAULT_LANGUAGE": get_site_property("DEFAULT_LANGUAGE", "en-US")
    }
