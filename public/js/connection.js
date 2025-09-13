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
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log("[WS] Disconnecting existing connection...");
      this.ws.close();
      this.ws = null;
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
    // 🔍 Debug trace to find all connection triggers
    console.trace(`[WS] connect() called with avatar=${avatarName}`);

    if (this.isConnected()) {
      console.log("[WS] Already connected — skipping duplicate connect");
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.host;
    const avatarParam = encodeURIComponent(avatarName || "FlowBot");
    const wsUrl = `${protocol}://${host}/ws/flowbot?avatar=${avatarParam}&session=${sessionId}`;

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

    this.ws.onerror = () => {
      console.warn("[WS] Error — falling back to SSE");
      this.connectSSE(sessionId);
    };

    this.ws.onclose = () => {
      console.log("[WS] Connection closed.");
      if (!this.usingSSE) {
        this.connectSSE(sessionId);
      }
    };
  },

  connectSSE(sessionId) {
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
    };
  },

  _updateStatus(message, color) {
    if (this.updateStatusFn) {
      this.updateStatusFn(message, color);
    }
  }
};