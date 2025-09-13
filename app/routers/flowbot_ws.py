"""
flowbot_ws.py — Router for FlowBot real-time endpoints.

Responsibilities:
- WebSocket endpoint for interactive FlowBot chat
- SSE endpoint for clients without WebSocket support
- HTTP POST endpoint for injecting messages into the SSE stream
- Logging for connection lifecycle and message flow

Future Enhancements:
- Authentication/authorization for multi-user sessions
- Room targeting and persona preview via query params
"""

from fastapi import APIRouter, WebSocket, Query, Request
from fastapi.responses import StreamingResponse

from app.core.logger import logger
from app.services import flowbot_service

router = APIRouter(tags=["FlowBot Chat"])

# ===== Utility =====
def get_client_host(source) -> str:
    return source.client.host if source.client else "unknown"

# ===== WebSocket Endpoint =====
@router.websocket("/ws/flowbot")
async def websocket_flowbot(
    websocket: WebSocket,
    avatar: str = Query("FlowBot", description="Avatar name to personalize the bot persona"),
    session: str = Query(..., description="Unique session/room identifier")
):
    """
    Handle a WebSocket connection for FlowBot chat.

    Args:
        websocket: Active WebSocket connection
        avatar: Avatar name to personalize the bot persona
        session: Unique session/room identifier
    """
    client_host = get_client_host(websocket)
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
    """
    Establish an SSE stream for clients without WebSocket support.

    Args:
        request: Incoming HTTP request
        session: Unique session/room identifier
    """
    client_host = get_client_host(request)
    logger.info(f"[SSE][{session}] Connection opened from {client_host}")

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
        payload: JSON body containing 'text' key
        request: Incoming HTTP request
        session: Unique session/room identifier
        avatar: Avatar name to personalize the bot persona

    Returns:
        dict: Status confirmation
    """
    client_host = get_client_host(request)
    text = payload.get("text", "").strip()

    logger.info(f"[SEND][{session}] Message from {client_host} (avatar={avatar}): {text!r}")

    await flowbot_service.handle_sse_send(session_id=session, text=text, avatar=avatar)
    return {"status": "sent"}