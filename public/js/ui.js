// /Public/js/ui.js
export let selected_avatar = {
  FLOWBOT_PREFERRED_NAME: "",
  FLOWBOT_AVATAR_ICON: "",
  FLOWBOT_AVATAR_DEMEANOR: ""
};

export function getDefaultAvatarIcon() {
  const defaultAv = (window.siteProps?.ALTERNATE_AVATARS || []).find(a => a.default);
  return defaultAv ? defaultAv.icon : "/static/flowbot-avatar.png";
}

export function addMessage(text, sender) {
  const messagesDiv = document.getElementById("messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = `msg ${sender}`;

  const avatar = document.createElement("img");
  avatar.className = "avatar";
  if (sender === "bot") {
    avatar.src = selected_avatar.FLOWBOT_AVATAR_ICON || getDefaultAvatarIcon();
    avatar.alt = selected_avatar.FLOWBOT_PREFERRED_NAME;
  } else {
    avatar.src = "/static/user-avatar.png";
    avatar.alt = "You";
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(bubble);
  messagesDiv.appendChild(msgDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

export function addSystemMessage(text) {
  const messagesDiv = document.getElementById("messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = "msg system";

  const bubble = document.createElement("div");
  bubble.className = "bubble system-bubble";
  bubble.textContent = text;

  msgDiv.appendChild(bubble);
  messagesDiv.appendChild(msgDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

export function updateSelectedUI() {
  const heading = document.getElementById("chat-heading");
  const selectedImg = document.querySelector("#dropdown-selected img");
  const selectedName = document.querySelector("#dropdown-selected .dropdown-name");

  heading.textContent = `💬 Chat with ${selected_avatar.FLOWBOT_PREFERRED_NAME}`;
  selectedImg.src = selected_avatar.FLOWBOT_AVATAR_ICON || getDefaultAvatarIcon();
  selectedImg.alt = selected_avatar.FLOWBOT_PREFERRED_NAME;
  selectedName.textContent = `${selected_avatar.FLOWBOT_PREFERRED_NAME} — ${selected_avatar.FLOWBOT_AVATAR_PERSONA}`;
  window.currentBotAvatar = selected_avatar.FLOWBOT_AVATAR_ICON || getDefaultAvatarIcon();
}

export function updateStatus(text, color, sessionId) {
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