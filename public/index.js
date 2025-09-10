// ─────────────────────────────────────────────────────────────
// 🍪 Cookie Utilities
// ─────────────────────────────────────────────────────────────
function setCookie(name, value, days) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${value};expires=${expires};path=/`;
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? match[2] : null;
}

// ─────────────────────────────────────────────────────────────
// 🆔 Session Management
// ─────────────────────────────────────────────────────────────
function generateSessionId() {
  return crypto.randomUUID();
}

function getSessionId() {
  let sessionId = getCookie("flowbotSessionId");
  if (!sessionId) {
    sessionId = generateSessionId();
    setCookie("flowbotSessionId", sessionId, 7);
  }
  return sessionId;
}

const sessionId = getSessionId();

// ─────────────────────────────────────────────────────────────
// ⚙️ Default Site Configuration
// ─────────────────────────────────────────────────────────────
const defaults = {
  FLOWBOT_PREFERRED_NAME: "FlowBot",
  SUPPORT_EMAIL: "support@permitflow.bettini.us",
  DEFAULT_LANGUAGE: "en-US",
  ALTERNATE_AVATARS: [
    {
      avatar: "FlowBot",
      demeanor: "Chippy",
      icon: "/static/flowbot-avatar.png"
    }
  ]
};

// ─────────────────────────────────────────────────────────────
// 👤 Avatar Selection State
// ─────────────────────────────────────────────────────────────
let selected_avatar = {
  FLOWBOT_PREFERRED_NAME: defaults.FLOWBOT_PREFERRED_NAME,
  FLOWBOT_AVATAR_ICON: defaults.ALTERNATE_AVATARS[0].icon,
  FLOWBOT_AVATAR_DEMEANOR: defaults.ALTERNATE_AVATARS[0].demeanor
};

// ─────────────────────────────────────────────────────────────
// 🌐 Connection State
// ─────────────────────────────────────────────────────────────
let ws = null;
let eventSource = null;
let usingSSE = false;

// ─────────────────────────────────────────────────────────────
// 🚀 DOM Ready
// ─────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const heading = document.getElementById("chat-heading");
  const dropdown = document.getElementById("avatar-dropdown");
  const dropdownSelected = document.getElementById("dropdown-selected");
  const dropdownList = document.getElementById("dropdown-list");
  const selectedImg = dropdownSelected.querySelector("img");
  const selectedName = dropdownSelected.querySelector(".dropdown-name");
  const messagesDiv = document.getElementById("messages");
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("send-btn");

  // 🟢 Connection Status Block
  const statusIndicator = document.createElement("div");
  statusIndicator.id = "connection-status";
  statusIndicator.style.fontSize = "0.8em";
  statusIndicator.style.marginBottom = "5px";
  messagesDiv.parentNode.insertBefore(statusIndicator, messagesDiv);

  // 🧠 Dropdown Toggle
  dropdownSelected.addEventListener("click", () => {
    dropdown.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove("open");
    }
  });

  // 🔧 Load Site Properties
  fetch("/site-properties")
    .then(res => res.json())
    .then(data => {
      const props = { ...defaults, ...data };

      if (!Array.isArray(props.ALTERNATE_AVATARS) || props.ALTERNATE_AVATARS.length === 0) {
        props.ALTERNATE_AVATARS = defaults.ALTERNATE_AVATARS;
      }

      const savedAvatarName = getCookie("selectedAvatar");
      const initial = props.ALTERNATE_AVATARS.find(a => a.avatar === savedAvatarName) || props.ALTERNATE_AVATARS[0];

      selected_avatar = {
        FLOWBOT_PREFERRED_NAME: initial.avatar,
        FLOWBOT_AVATAR_ICON: initial.icon,
        FLOWBOT_AVATAR_DEMEANOR: initial.demeanor
      };

      props.ALTERNATE_AVATARS.forEach(av => {
        const item = document.createElement("div");
        item.className = "dropdown-item";
        item.innerHTML = `<img src="${av.icon}" alt="${av.avatar}"><span>${av.avatar} — ${av.demeanor}</span>`;
        item.addEventListener("click", () => {
          const oldName = selected_avatar.FLOWBOT_PREFERRED_NAME;
          selected_avatar = {
            FLOWBOT_PREFERRED_NAME: av.avatar,
            FLOWBOT_AVATAR_ICON: av.icon,
            FLOWBOT_AVATAR_DEMEANOR: av.demeanor
          };
          setCookie("selectedAvatar", av.avatar, 365);
          updateSelectedUI();
          dropdown.classList.remove("open");
          addSystemMessage(`(${oldName} helper now changed to ${selected_avatar.FLOWBOT_PREFERRED_NAME}...)`);
        });
        dropdownList.appendChild(item);
      });

      updateSelectedUI();

      const supportBtn = document.getElementById("support-email-btn");
      if (props.SUPPORT_EMAIL) {
        supportBtn.textContent = "Email PermitFlow Support";
        supportBtn.style.display = "inline-block";
        supportBtn.addEventListener("click", () => {
          window.location.href = `mailto:${props.SUPPORT_EMAIL}`;
        });
      }

      connectWebSocket();
    })
    .catch(err => {
      console.error("Error loading site properties:", err);
      updateSelectedUI();
    });

  // ─────────────────────────────────────────────────────────────
  // 🔌 Connection Logic
  // ─────────────────────────────────────────────────────────────
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const avatarParam = encodeURIComponent(selected_avatar.FLOWBOT_PREFERRED_NAME);
    ws = new WebSocket(`${protocol}://${window.location.host}/ws/flowbot?avatar=${avatarParam}&session=${sessionId}`);

    ws.onopen = () => {
      usingSSE = false;
      updateStatus("Connected via WebSocket", "green");
      console.log(`[WS] Connected. Session ID: ${sessionId}`);
    };

    ws.onmessage = (event) => {
      addMessage(event.data, "bot");
    };

    ws.onerror = () => {
      console.warn("WebSocket error — falling back to SSE");
      connectSSE();
    };

    ws.onclose = () => {
      if (!usingSSE) {
        console.warn("WebSocket closed — falling back to SSE");
        connectSSE();
      }
    };
  }

  function connectSSE() {
    usingSSE = true;
    eventSource = new EventSource(`/events?session=${sessionId}`);

    eventSource.onopen = () => {
      updateStatus("Connected via SSE", "orange");
    };

    eventSource.onmessage = (event) => {
      addMessage(event.data, "bot");
    };

    eventSource.onerror = () => {
      updateStatus("Disconnected", "red");
      eventSource.close();
    };
  }

  // ─────────────────────────────────────────────────────────────
  // 📤 Send Message
  // ─────────────────────────────────────────────────────────────
  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    if (!usingSSE && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(text);
    } else {
      fetch(`/send?session=${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
    }

    addMessage(text, "user");
    input.value = "";
  }

  // ─────────────────────────────────────────────────────────────
  // 💬 UI Helpers
  // ─────────────────────────────────────────────────────────────
  function addMessage(text, sender) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `msg ${sender}`;

    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src = sender === "bot"
      ? (selected_avatar.FLOWBOT_AVATAR_ICON || defaults.ALTERNATE_AVATARS[0].icon)
      : "/static/user-avatar.png";
    avatar.alt = sender === "bot"
      ? selected_avatar.FLOWBOT_PREFERRED_NAME
      : "You";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function addSystemMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "msg system";

    const bubble = document.createElement("div");
    bubble.className = "bubble system-bubble";
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function updateSelectedUI() {
    heading.textContent = `💬 Chat with ${selected_avatar.FLOWBOT_PREFERRED_NAME}`;
    selectedImg.src = selected_avatar.FLOWBOT_AVATAR_ICON;
    selectedImg.alt = selected_avatar.FLOWBOT_PREFERRED_NAME;
    selectedName.textContent = `${selected_avatar.FLOWBOT_PREFERRED_NAME} — ${selected_avatar.FLOWBOT_AVATAR_DEMEANOR}`;
    window.currentBotAvatar = selected_avatar.FLOWBOT_AVATAR_ICON;
  }

  function updateStatus(text, color) {
    const statusText = document.getElementById("status-text");
    const badge = document.getElementById("session-id-badge");

    if (statusText) {
      statusText.textContent = text;
      statusText.style.color = color;
    }

    if (badge && typeof sessionId !== "undefined") {
      badge.textContent = `Session: ${sessionId}`;
      badge.style.display = "inline";
    }
  }

  // ─────────────────────────────────────────────────────────────
  // 🖱️ Event Listeners for Sending Messages
  // ─────────────────────────────────────────────────────────────
  sendBtn.addEventListener("click", sendMessage);

  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
});