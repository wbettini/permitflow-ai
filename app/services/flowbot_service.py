"""
flowbot_service.py — Connection orchestration for FlowBot over WS and SSE.

Responsibilities:
- Manage WebSocket and Server-Sent Events (SSE) client connections.
- Instantiate FlowBot with correct tone based on avatar mapping.
- Broadcast messages to all clients in a session (WS + SSE).
- Send proactive greeting on connect.
- Provide helper for processing SSE POST messages.

Future Changes:
- Add per-session context persistence.
- Support targeted broadcasts to specific clients.
- Integrate authentication for multi-user environments.
"""

import asyncio
from typing import Dict, Set
from fastapi import WebSocket
from sse_starlette.sse import EventSourceResponse

from app.agents.flowbot.flowbot import FlowBot
from app.core.logger import logger

# ===== Avatar to Tone Mapping =====
avatar_to_tone_map = {
    "FlowBot": "chippy",
    "Alexandra": "mentor",
    "Robert": "formal",
    "Emily": "chippy"
}

# ===== Client Tracking =====
ws_clients: Dict[str, Set[WebSocket]] = {}
sse_clients: Dict[str, Set[asyncio.Queue]] = {}

# ===== Broadcast Helper =====
async def broadcast_message(session_id: str, message: str):
    """Send a message to all WS and SSE clients in the session."""
    logger.info(f"[BROADCAST][{session_id}] {message!r}")

    # WS clients
    for ws in list(ws_clients.get(session_id, [])):
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.warning(f"[WS][{session_id}] Broadcast failed: {e}")
            ws_clients[session_id].discard(ws)

    # SSE clients
    for queue in list(sse_clients.get(session_id, [])):
        try:
            await queue.put(message)
        except Exception as e:
            logger.warning(f"[SSE][{session_id}] Broadcast failed: {e}")
            sse_clients[session_id].discard(queue)

# ===== WebSocket Connection Handler =====
async def handle_ws_connection(websocket: WebSocket, avatar: str, session_id: str):
    """Manage a single WebSocket connection for FlowBot."""
    await websocket.accept()
    ws_clients.setdefault(session_id, set()).add(websocket)

    tone = avatar_to_tone_map.get(avatar, "default")
    bot = FlowBot(user_id=session_id, tone=tone)

    logger.info(f"[WS][{session_id}] Client connected (avatar={avatar}, tone={tone})")

    # Proactive greeting — tone-aware and placeholder-ready
    greeting = bot._get_greeting().format(**bot._placeholder_values())
    await broadcast_message(session_id, greeting)

    try:
        while True:
            message_text = await websocket.receive_text()
            logger.info(f"[WS][{session_id}] Received: {message_text}")
            reply_text = bot.handle_message(message_text)
            await broadcast_message(session_id, reply_text)

    except Exception as e:
        logger.exception(f"[WS][{session_id}] Connection error: {e}")
    finally:
        ws_clients[session_id].discard(websocket)
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"[WS][{session_id}] Connection closed (avatar={avatar})")

# ===== SSE Event Stream =====
async def sse_event_stream(session_id: str):
    """Async generator for SSE connections."""
    queue: asyncio.Queue[str] = asyncio.Queue()
    sse_clients.setdefault(session_id, set()).add(queue)
    logger.info(f"[SSE][{session_id}] Client connected (total SSE clients: {len(sse_clients[session_id])})")

    async def event_generator():
        try:
            while True:
                message = await queue.get()
                yield {"event": "message", "data": message}
        except asyncio.CancelledError:
            pass
        finally:
            sse_clients[session_id].discard(queue)
            logger.info(f"[SSE][{session_id}] Client disconnected")

    return EventSourceResponse(event_generator())

# ===== SSE Send Helper =====
async def handle_sse_send(session_id: str, text: str, avatar: str):
    """Process a message received via HTTP POST and broadcast it."""
    tone = avatar_to_tone_map.get(avatar, "default")
    bot = FlowBot(user_id=session_id, tone=tone)

    logger.info(f"[SSE][{session_id}] Processing POST message from avatar={avatar}, tone={tone}: {text!r}")

    reply_text = bot.handle_message(text)
    await broadcast_message(session_id=session_id, message=reply_text)