// /public/js/connection.js
export const ConnectionManager = {
  ws: null,
  eventSource: null,
  usingSSE: false,
  messageQueue: [],
  uiReady: false,
  addMessageFn: null,
  updateStatusFn: null,

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  },

  disconnect() {
    if (this.ws) {
      console.log("[WS] Closing WebSocket connection...");
      this.ws.close();
      this.ws = null;
    }
    if (this.eventSource) {
      console.log("[SSE] Closing SSE connection...");
      this.eventSource.close();
      this.eventSource = null;
    }
  },

  flushQueue() {
    if (this.addMessageFn) {
      this.messageQueue.forEach(msg => this.addMessageFn(msg, "bot"));
    }
    this.messageQueue = [];
  },

  handleIncomingMessage(data) {
    if (this.uiReady && this.addMessageFn) {
      this.addMessageFn(data, "bot");
    } else {
      this.messageQueue.push(data);
    }
  },

  connect(sessionId, avatarName) {
    console.trace(`[WS] connect() called with avatar=${avatarName}`);

    if (this.isConnected()) {
      console.log("[WS] Already connected — skipping duplicate connect");
      return;
    }

    // Always close SSE before starting WS
    if (this.eventSource) {
      console.log("[WS] Closing SSE before opening WebSocket...");
      this.eventSource.close();
      this.eventSource = null;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.host;
    const avatarParam = encodeURIComponent(avatarName || "FlowBot");
    const wsUrl = `${protocol}://${host}/ws/flowbot?avatar=${avatarParam}&session=${sessionId}`;

    console.log(`[WS] Connecting to ${wsUrl}`);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.usingSSE = false;
      this._updateStatus("Connected via WebSocket", "green");
      console.log(`[WS] Connected. Session ID: ${sessionId}, Avatar: ${avatarName}`);
    };

    this.ws.onmessage = (event) => {
      console.log("[WS] Received:", event.data);
      this.handleIncomingMessage(event.data);
    };

    this.ws.onerror = (err) => {
      console.warn("[WS] Error — falling back to SSE", err);
      this._startSSE(sessionId);
    };

    this.ws.onclose = () => {
      console.log("[WS] Connection closed.");
      if (!this.usingSSE) {
        this._startSSE(sessionId);
      }
    };
  },

  _startSSE(sessionId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log("[SSE] Skipping SSE — WS is active");
      return;
    }
    if (this.eventSource) {
      console.log("[SSE] Already connected — skipping duplicate SSE");
      return;
    }

    console.log("[SSE] Starting SSE connection...");
    this.usingSSE = true;
    this.eventSource = new EventSource(`/events?session=${sessionId}`);

    this.eventSource.onopen = () => {
      this._updateStatus("Connected via SSE", "orange");
      console.log(`[SSE] Connected. Session ID: ${sessionId}`);
    };

    this.eventSource.onmessage = (event) => {
      console.log("[SSE] Received:", event.data);
      this.handleIncomingMessage(event.data);
    };

    this.eventSource.onerror = () => {
      this._updateStatus("Disconnected", "red");
      console.warn("[SSE] Error — connection closed");
      this.eventSource.close();
      this.eventSource = null;
    };
  },

  _updateStatus(message, color) {
    if (this.updateStatusFn) {
      this.updateStatusFn(message, color);
    }
  }
};