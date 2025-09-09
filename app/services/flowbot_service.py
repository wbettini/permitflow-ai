"""
flowbot_service.py — Service layer for FlowBot chat.

Responsibilities:
- Manage WebSocket and SSE client connections.
- Broadcast messages to all connected clients (WS + SSE).
- Maintain short message history for new connections.
- Initialize and run FlowBot conversation loop.
- Log all connection events, broadcasts, and errors via centralized logger.

Future Changes:
- Replace JSON-based prompt loading with Azure DB queries.
- Add authentication/authorization for multi-user sessions.
- Implement per-session state isolation for multi-room support.
"""

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from typing import List, AsyncGenerator
from asyncio import Queue
from app.core.config import load_site_properties, TOLLGATE_PROMPTS_FILE
from app.core.state_manager import StateManager
from app.core.logger import logger
from app.agents.flowbot.flowbot import FlowBot

# ===== Connection State =====
ws_clients: List[WebSocket] = []       # Active WebSocket connections
sse_clients: List[Queue] = []          # Queues for SSE clients
message_history: List[str] = []        # Recent messages for new clients
MESSAGE_HISTORY_LIMIT = 20             # Keep last N messages for replay


# ===== Broadcast Utilities =====
async def broadcast_message(message: str):
    """
    Send a message to all connected WS and SSE clients.

    Args:
        message (str): The message text to broadcast.

    Notes:
        - Stores message in history for replay to new clients.
        - Removes clients from lists if send fails.
    """
    logger.info(f"[BROADCAST] {message!r}")

    # Store in history (bounded)
    message_history.append(message)
    if len(message_history) > MESSAGE_HISTORY_LIMIT:
        message_history.pop(0)

    # Send to WebSocket clients
    for ws in list(ws_clients):
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.warning(f"[WS] Failed to send to {ws.client}: {e}")
            ws_clients.remove(ws)

    # Send to SSE clients
    for queue in list(sse_clients):
        try:
            await queue.put(message)
        except Exception as e:
            logger.warning(f"[SSE] Failed to send to client queue: {e}")
            sse_clients.remove(queue)


# ===== WebSocket Handler =====
async def handle_ws_connection(websocket: WebSocket, avatar: str = None):
    """
    Accepts a WebSocket connection and runs the FlowBot conversation loop.

    Args:
        websocket (WebSocket): The active WebSocket connection.
        avatar (str, optional): Avatar name to personalize the bot persona.

    Flow:
        1. Accept connection and log open.
        2. Load site properties and select avatar.
        3. Initialize FlowBot with required fields and prompt file.
        4. Send greeting via broadcast.
        5. Loop to receive messages and send replies until process completes.
        6. Handle disconnects and errors gracefully.
    """
    await websocket.accept()
    ws_clients.append(websocket)

    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"[WS] Client connected: {client_host} (avatar={avatar})")

    props = load_site_properties()

    # Match avatar from query param if provided, else default
    selected_avatar = None
    if avatar:
        selected_avatar = next(
            (a for a in props["ALTERNATE_AVATARS"] if a["avatar"] == avatar),
            None
        )
    if not selected_avatar:
        selected_avatar = props["ALTERNATE_AVATARS"][0]

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
    await broadcast_message(greeting)

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"[WS] Received from {client_host}: {data!r}")

            # First message = permit type
            if not state.get("permit_type"):
                if not data.lower().startswith("permit to"):
                    await websocket.send_text(
                        "Which type of permit are we working on? "
                        "For example: Permit to Design, Permit to Build, Permit to Operate."
                    )
                    continue
                start_msg = bot.start(data)
                await broadcast_message(start_msg)
                continue

            # Subsequent messages
            reply = bot.converse(data)
            await broadcast_message(reply)

            # Optional: detect end of process
            if bot.current_tollgate == 3 and "Process complete" in reply:
                logger.info(f"[WS] Process complete for {client_host}")
                break

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: {client_host}")
    except Exception as e:
        logger.error(f"[WS] Error for {client_host}: {e}", exc_info=True)
        try:
            if websocket.application_state.name != "DISCONNECTED":
                await websocket.send_text(f"⚠️ Error: {e}")
        except RuntimeError:
            pass  # Socket already closed
    finally:
        if websocket in ws_clients:
            ws_clients.remove(websocket)
        logger.info(f"[WS] Connection cleanup complete for {client_host}")


# ===== SSE Handler =====
async def sse_event_stream() -> AsyncGenerator[str, None]:
    """
    Async generator for SSE clients.

    Flow:
        1. Add client queue to sse_clients list.
        2. Send message history immediately.
        3. Yield new messages as they arrive.
        4. Remove client on disconnect.
    """
    queue: Queue = Queue()
    sse_clients.append(queue)
    logger.info(f"[SSE] Client connected (total SSE clients: {len(sse_clients)})")

    # Send history to new client
    for msg in message_history:
        yield f"data: {msg}\n\n"

    try:
        while True:
            msg = await queue.get()
            yield f"data: {msg}\n\n"
    except Exception as e:
        logger.warning(f"[SSE] Stream error: {e}")
    finally:
        if queue in sse_clients:
            sse_clients.remove(queue)
        logger.info(f"[SSE] Client disconnected (total SSE clients: {len(sse_clients)})")


# ===== SSE Send Handler =====
async def handle_sse_send(text: str):
    """
    Handle incoming message from SSE client via HTTP POST.

    Args:
        text (str): The message text to broadcast.
    """
    logger.info(f"[SEND] Received SSE POST message: {text!r}")
    await broadcast_message(text)