"""
🧠 FlowBot Service — WS & SSE Orchestration

Responsibilities:
- Manage WebSocket and SSE client connections
- Instantiate FlowBot with persona-aware avatar
- Broadcast messages to all clients in a session
- Send proactive greeting on connect
- Support dynamic persona switching and fallback injection
"""

import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState
from sse_starlette.sse import EventSourceResponse

from app.agents.flowbot.flowbot import FlowBot
from app.prompts.flowbot_prompts import AVATAR_MAP, PERSONAS
from app.core.logger import logger

# ===== Client Tracking =====
ws_clients: Dict[str, Set[WebSocket]] = {}
sse_clients: Dict[str, Set[asyncio.Queue]] = {}


# ===== Broadcast Helper =====
async def broadcast_message(session_id: str, message: str) -> None:
    """Send a message to all WS and SSE clients in the session."""
    logger.info(f"[BROADCAST][{session_id}] {message!r}")

    # WS clients
    for ws in list(ws_clients.get(session_id, [])):
        try:
            if ws.application_state == WebSocketState.CONNECTED:
                await ws.send_text(message)
            else:
                logger.debug(f"[WS][{session_id}] Skipping closed connection")
                ws_clients[session_id].discard(ws)
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


# ===== Persona Switching Helper =====
def get_persona_switch(message: str) -> Optional[str]:
    """Return a persona key if the message contains a switch trigger."""
    msg_lower = message.lower()
    for persona_key, persona_data in PERSONAS.items():
        for trigger in persona_data.get("switch_triggers", []):
            if trigger in msg_lower:
                return persona_key
    return None


# ===== WebSocket Connection Handler =====
async def handle_ws_connection(websocket: WebSocket, avatar: str, session_id: str) -> None:
    """Manage a single WebSocket connection for FlowBot."""
    await websocket.accept()
    ws_clients.setdefault(session_id, set()).add(websocket)

    if avatar not in AVATAR_MAP:
        logger.warning(f"[WS][{session_id}] Unknown avatar '{avatar}', defaulting to 'default'")

    bot = FlowBot(user_id=session_id, avatar=avatar)
    logger.info(f"[WS][{session_id}] Client connected (avatar={avatar})")

    # Proactive greeting
    greeting = bot._get_greeting().format(**bot._placeholder_values())
    await broadcast_message(session_id, greeting)

    try:
        while True:
            message_text = await websocket.receive_text()
            logger.info(f"[WS][{session_id}] Received: {message_text}")

            # Persona switching (data-driven)
            new_persona = get_persona_switch(message_text)
            if new_persona:
                logger.info(f"[WS][{session_id}] Persona switch → {new_persona}")
                avatar = new_persona
                bot = FlowBot(user_id=session_id, avatar=avatar)

            # Handle message
            reply_text = await bot.handle_message(message_text)

            # Fallback injection
            if not reply_text.strip():
                logger.warning(f"[WS][{session_id}] Empty response — injecting fallback persona")
                fallback_avatar = "resilient"
                bot = FlowBot(user_id=session_id, avatar=fallback_avatar)
                reply_text = await bot.handle_message(
                    "Sorry, we lost connection. Want to pick up where we left off?"
                )

            await broadcast_message(session_id, reply_text)

    except WebSocketDisconnect as e:
        logger.info(f"[WS][{session_id}] Client disconnected cleanly: {e.code}")
    except Exception as e:
        logger.exception(f"[WS][{session_id}] Connection error: {e}")
        if websocket.application_state == WebSocketState.CONNECTED:
            fallback_avatar = "empathetic"
            bot = FlowBot(user_id=session_id, avatar=fallback_avatar)
            fallback_msg = await bot.handle_message(
                "Something went wrong, but I'm here to help you get back on track."
            )
            await broadcast_message(session_id, fallback_msg)
    finally:
        ws_clients[session_id].discard(websocket)
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info(f"[WS][{session_id}] Connection closed (avatar={avatar})")


# ===== SSE Event Stream =====
async def sse_event_stream(session_id: str) -> EventSourceResponse:
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
async def handle_sse_send(session_id: str, text: str, avatar: str) -> None:
    """Process a message received via HTTP POST and broadcast it."""
    if avatar not in AVATAR_MAP:
        logger.warning(f"[SSE][{session_id}] Unknown avatar '{avatar}', defaulting to 'default'")

    bot = FlowBot(user_id=session_id, avatar=avatar)
    logger.info(f"[SSE][{session_id}] Processing POST message from avatar={avatar}: {text!r}")

    reply_text = await bot.handle_message(text)

    if not reply_text.strip():
        logger.warning(f"[SSE][{session_id}] Empty response — injecting fallback persona")
        fallback_avatar = "resilient"
        bot = FlowBot(user_id=session_id, avatar=fallback_avatar)
        reply_text = await bot.handle_message(
            "Sorry, we lost connection. Want to pick up where we left off?"
        )

    await broadcast_message(session_id=session_id, message=reply_text)