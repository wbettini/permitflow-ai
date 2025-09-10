"""
main.py — Application entry point for PermitFlow-AI.

Responsibilities:
- Create FastAPI app instance.
- Mount routers for WebSocket chat, site properties, and tollgate prompts.
- Serve static assets and health/version endpoints.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from app.routers import flowbot_ws, site_properties

# -------------------------
# FastAPI App Initialization
# -------------------------
app = FastAPI(title="PermitFlow-AI", version="0.2.0")
print("🚀 FlowBot is live and listening...")

# -------------------------
# Mount Routers
# -------------------------
app.include_router(flowbot_ws.router)
app.include_router(site_properties.router)

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