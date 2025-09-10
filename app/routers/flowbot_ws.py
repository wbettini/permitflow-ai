"""
flowbot_ws.py — Router for FlowBot real-time endpoints.

Responsibilities:
- Expose WebSocket endpoint for interactive FlowBot chat.
- Expose SSE endpoint for clients without WebSocket support.
- Expose HTTP POST endpoint for sending messages into the SSE stream.
- Log connection opens/closes and messages for debugging and monitoring.

Future Changes:
- Add authentication/authorization for multi-user sessions.
- Support query parameters for session IDs or room targeting.
"""

from fastapi import APIRouter, WebSocket, Query, Request
from fastapi.responses import StreamingResponse

from app.core.logger import logger
from app.services import flowbot_service

router = APIRouter(tags=["FlowBot Chat"])

# ===== WebSocket Endpoint =====
@router.websocket("/ws/flowbot")
async def websocket_flowbot(
    websocket: WebSocket,
    avatar: str = Query(None, description="Avatar name to personalize the bot persona"),
    session: str = Query(..., description="Unique session/room identifier")
):
    """
    Handle a WebSocket connection for FlowBot chat.

    Args:
        websocket (WebSocket): Active WebSocket connection.
        avatar (str, optional): Avatar name to personalize the bot persona.
        session (str): Unique session/room identifier for isolating conversations.

    Flow:
        1. Log connection open.
        2. Delegate handling to flowbot_service.handle_ws_connection().
        3. Log connection close in finally block.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"[WS][{session}] Connection opened from {client_host} (avatar={avatar})")

    try:
        await flowbot_service.handle_ws_connection(websocket, avatar, session_id=session)
    finally:
        logger.info(f"[WS][{session}] Connection closed from {client_host} (avatar={avatar})")


# ===== SSE Endpoint =====
@router.get("/events")
async def sse_events(
    request: Request,
    session: str = Query(..., description="Unique session/room identifier")
):
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"[SSE][{session}] Connection opened from {client_host}")

    # Just return the EventSourceResponse directly
    return await flowbot_service.sse_event_stream(session_id=session)

# ===== SSE Send Endpoint =====
@router.post("/send")
async def send_message(
    payload: dict,
    request: Request,
    session: str = Query(..., description="Unique session/room identifier"),
    avatar: str = Query("FlowBot", description="Avatar name to personalize the bot persona")
):
    """
    Accept a message via HTTP POST and broadcast it to all SSE clients in the same session.

    Args:
        payload (dict): JSON body containing 'text' key.
        request (Request): Incoming HTTP request.
        session (str): Unique session/room identifier for isolating broadcasts.
        avatar (str): Avatar name to personalize the bot persona.

    Returns:
        dict: Status confirmation.
    """
    client_host = request.client.host if request.client else "unknown"
    text = payload.get("text", "")

    logger.info(f"[SEND][{session}] Message from {client_host} (avatar={avatar}): {text!r}")

    await flowbot_service.handle_sse_send(session_id=session, text=text, avatar=avatar)
    return {"status": "sent"}