"""
flowbot_service.py — Service layer for FlowBot chat.

Responsibilities:
- Manage WebSocket and SSE client connections.
- Broadcast messages to the correct session's clients (WS + SSE).
- Maintain short message history per session for new connections.
- Initialize and run FlowBot conversation loop.
- Log all connection events, broadcasts, and errors via centralized logger.

Future Changes:
- Replace JSON-based prompt loading with Azure DB queries.
- Add authentication/authorization for multi-user sessions.
- Implement multi-room support with persistent state.
"""

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from typing import Dict, Set, AsyncGenerator
from asyncio import Queue
from collections import defaultdict

from app.core.config import load_site_properties, TOLLGATE_PROMPTS_FILE
from app.core.state_manager import StateManager
from app.core.logger import logger
from app.agents.flowbot.flowbot import FlowBot

# ===== Connection State =====
ws_clients: Dict[str, Set[WebSocket]] = defaultdict(set)   # session_id -> active WS connections
sse_clients: Dict[str, Set[Queue]] = defaultdict(set)      # session_id -> SSE queues
message_history: Dict[str, list[str]] = defaultdict(list)  # session_id -> recent messages
MESSAGE_HISTORY_LIMIT = 20                                 # Keep last N messages per session


# ===== Broadcast Utilities =====
async def broadcast_message(session_id: str, message: str) -> None:
    """
    Send a message to all connected WS and SSE clients in a given session.

    Args:
        session_id (str): The session/room identifier.
        message (str): The message text to broadcast.

    Notes:
        - Stores message in per-session history for replay to new clients.
        - Removes clients from lists if send fails.
    """
    logger.info(f"[BROADCAST][{session_id}] {message!r}")

    # Store in history (bounded)
    history = message_history[session_id]
    history.append(message)
    if len(history) > MESSAGE_HISTORY_LIMIT:
        history.pop(0)

    # Send to WebSocket clients
    for ws in list(ws_clients[session_id]):
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.warning(f"[WS][{session_id}] Failed to send to {ws.client}: {e}")
            ws_clients[session_id].discard(ws)

    # Send to SSE clients
    for queue in list(sse_clients[session_id]):
        try:
            await queue.put(message)
        except Exception as e:
            logger.warning(f"[SSE][{session_id}] Failed to send to client queue: {e}")
            sse_clients[session_id].discard(queue)


# ===== WebSocket Handler =====
async def handle_ws_connection(websocket: WebSocket, avatar: str, session_id: str) -> None:
    """
    Accepts a WebSocket connection and runs the FlowBot conversation loop.

    Args:
        websocket (WebSocket): The active WebSocket connection.
        avatar (str): Avatar name to personalize the bot persona.
        session_id (str): Unique session/room identifier.

    Flow:
        1. Accept connection and log open.
        2. Load site properties and select avatar.
        3. Initialize FlowBot with required fields and prompt file.
        4. Send greeting via broadcast to this session only.
        5. Loop to receive messages and send replies until process completes.
        6. Handle disconnects and errors gracefully.
    """
    await websocket.accept()
    ws_clients[session_id].add(websocket)

    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"[WS][{session_id}] Client connected: {client_host} (avatar={avatar})")

    props = load_site_properties()

    # Match avatar from query param if provided, else default
    selected_avatar = next(
        (a for a in props["ALTERNATE_AVATARS"] if a["avatar"] == avatar),
        props["ALTERNATE_AVATARS"][0]
    )

    # Required fields for FlowBot's workflow
    required_fields = ["service_name", "owner", "data_classification"]

    # Initialize state manager and FlowBot instance
    state = StateManager()
    bot = FlowBot(state, required_fields, prompts_file=TOLLGATE_PROMPTS_FILE)

    # Dynamic greeting
    greeting = (
        f"👋 Hi, I'm {selected_avatar['avatar']}! "
        "What type of 'Permit to...' are we working on today?"
    )
    await broadcast_message(session_id, greeting)

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"[WS][{session_id}] Received from {client_host}: {data!r}")

            # First message = permit type
            if not state.get("permit_type"):
                if not data.lower().startswith("permit to"):
                    await websocket.send_text(
                        "Which type of permit are we working on? "
                        "For example: Permit to Design, Permit to Build, Permit to Operate."
                    )
                    continue
                start_msg = bot.start(data)
                await broadcast_message(session_id, start_msg)
                continue

            # Subsequent messages
            reply = bot.converse(data)
            await broadcast_message(session_id, reply)

            # Optional: detect end of process
            if bot.current_tollgate == 3 and "Process complete" in reply:
                logger.info(f"[WS][{session_id}] Process complete for {client_host}")
                break

    except WebSocketDisconnect:
        logger.info(f"[WS][{session_id}] Client disconnected: {client_host}")
    except Exception as e:
        logger.error(f"[WS][{session_id}] Error for {client_host}: {e}", exc_info=True)
        try:
            if websocket.application_state.name != "DISCONNECTED":
                await websocket.send_text(f"⚠️ Error: {e}")
        except RuntimeError:
            pass  # Socket already closed
    finally:
        ws_clients[session_id].discard(websocket)
        if not ws_clients[session_id]:
            ws_clients.pop(session_id, None)
            message_history.pop(session_id, None)
        logger.info(f"[WS][{session_id}] Connection cleanup complete for {client_host}")


# ===== SSE Handler =====
async def sse_event_stream(session_id: str) -> AsyncGenerator[str, None]:
    """
    Async generator for SSE clients.

    Flow:
        1. Add client queue to sse_clients[session_id].
        2. Send per-session message history immediately.
        3. Yield new messages as they arrive.
        4. Remove client on disconnect.
    """
    queue: Queue = Queue()
    sse_clients[session_id].add(queue)
    logger.info(f"[SSE][{session_id}] Client connected (total SSE clients: {len(sse_clients[session_id])})")

    # Send history to new client
    for msg in message_history[session_id]:
        yield f"data: {msg}\n\n"

    try:
        while True:
            msg = await queue.get()
            yield f"data: {msg}\n\n"
    except Exception as e:
        logger.warning(f"[SSE][{session_id}] Stream error: {e}")
    finally:
        sse_clients[session_id].discard(queue)
        if not sse_clients[session_id]:
            sse_clients.pop(session_id, None)
        logger.info(f"[SSE][{session_id}] Client disconnected (total SSE clients: {len(sse_clients.get(session_id, []))})")


# ===== SSE Send Handler =====
async def handle_sse_send(session_id: str, text: str) -> None:
    """
    Handle incoming message from SSE client via HTTP POST.

    Args:
        session_id (str): The session/room identifier.
        text (str): The message text to broadcast.
    """
    logger.info(f"[SEND][{session_id}] Received SSE POST message: {text!r}")
    await broadcast_message(session_id, text)