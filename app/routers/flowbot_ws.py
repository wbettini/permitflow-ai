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
from ..services import flowbot_service

router = APIRouter(tags=["FlowBot Chat"])


# ===== WebSocket Endpoint =====
@router.websocket("/ws/flowbot")
async def websocket_flowbot(websocket: WebSocket, avatar: str = Query(None)):
    """
    Handle a WebSocket connection for FlowBot chat.

    Args:
        websocket (WebSocket): The active WebSocket connection.
        avatar (str, optional): Avatar name to personalize the bot persona.

    Flow:
        1. Log connection open.
        2. Delegate handling to flowbot_service.handle_ws_connection().
        3. Log connection close in finally block.
    """
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"[WS] Connection opened from {client_host} (avatar={avatar})")
    try:
        await flowbot_service.handle_ws_connection(websocket, avatar)
    finally:
        logger.info(f"[WS] Connection closed from {client_host} (avatar={avatar})")


# ===== SSE Endpoint =====
@router.get("/events")
async def sse_events(request: Request):
    """
    Handle an SSE (Server-Sent Events) connection for FlowBot chat.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        StreamingResponse: Continuous stream of chat messages.

    Notes:
        - SSE is a fallback for clients without WebSocket support.
        - Connection close logging happens in the generator's finally block.
    """
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"[SSE] Connection opened from {client_host}")
    return StreamingResponse(
        flowbot_service.sse_event_stream(),
        media_type="text/event-stream"
    )


# ===== SSE Send Endpoint =====
@router.post("/send")
async def send_message(payload: dict, request: Request):
    """
    Accept a message via HTTP POST and broadcast it to all SSE clients.

    Args:
        payload (dict): JSON body containing 'text' key.
        request (Request): The incoming HTTP request.

    Returns:
        dict: Status confirmation.
    """
    client_host = request.client.host if request.client else "unknown"
    text = payload.get("text", "")
    logger.info(f"[SEND] Message from {client_host}: {text!r}")
    await flowbot_service.handle_sse_send(text)
    return {"status": "sent"}