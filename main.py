from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import json
from pathlib import Path

from core.state_manager import StateManager
from agents.flowbot.flowbot import FlowBot

# -------------------------
# FastAPI App Initialization
# -------------------------
app = FastAPI(title="PermitFlow-AI", version="0.2.0")
print("🚀 FlowBot is live and listening...")

# -------------------------
# Defaults for site properties
# -------------------------
defaults = {
    "FLOWBOT_PREFERRED_NAME": "FlowBot",
    "SUPPORT_EMAIL": "support.permitflow@bettini.us",
    "DEFAULT_LANGUAGE": "en-US",
    "ALTERNATE_AVATARS": [
        {"avatar": "FlowBot", "demeanor": "Chippy", "icon": "/static/flowbot-avatar.png"}
    ]
}

def load_site_properties():
    """Load site_properties.json merged with defaults."""
    json_path = Path("permitFlowDb/site_properties.json")
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**defaults, **data}
    return defaults

# -------------------------
# WebSocket: FlowBot Live Chat
# -------------------------
@app.websocket("/ws/flowbot")
async def websocket_flowbot(websocket: WebSocket, avatar: str = Query(None)):
    await websocket.accept()

    props = load_site_properties()

    # Match avatar from query param if provided
    selected_avatar = None
    if avatar:
        selected_avatar = next((a for a in props["ALTERNATE_AVATARS"] if a["avatar"] == avatar), None)
    if not selected_avatar:
        selected_avatar = props["ALTERNATE_AVATARS"][0]

    required_fields = ["service_name", "owner", "data_classification"]
    state = StateManager()
    bot = FlowBot(state, required_fields, prompts_file="permitFlowDb/tollgate_prompts.json")

    # Dynamic greeting using selected avatar name
    await websocket.send_text(
        f"👋 Hi, I'm {selected_avatar['avatar']}! What type of 'Permit to...' are we working on today?"
    )

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
# Site Properties Endpoint
# -------------------------
@app.get("/site-properties")
def site_properties():
    return load_site_properties()

# -------------------------
# Tollgate Prompts Endpoint
# -------------------------
@app.get("/tollgate-prompts")
def tollgate_prompts():
    json_path = Path("permitFlowDb/tollgate_prompts.json")
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"error": "tollgate_prompts.json not found"}