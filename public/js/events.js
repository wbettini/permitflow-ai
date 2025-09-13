import { selected_avatar, updateSelectedUI, addSystemMessage } from './ui.js';
import { SessionManager } from './session.js';

export function initUI(siteProps, sessionId, ConnectionManager) {
  const dropdown = document.getElementById("avatar-dropdown");
  const dropdownSelected = document.getElementById("dropdown-selected");
  const dropdownList = document.getElementById("dropdown-list");
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("send-btn");
  const supportBtn = document.getElementById("support-email-btn");

  // 🧠 Dropdown toggle behavior
  dropdownSelected.addEventListener("click", () => dropdown.classList.toggle("open"));
  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target)) dropdown.classList.remove("open");
  });

  // 🧠 Apply avatar selection to global state
  function applyAvatarSelection(av) {
    selected_avatar.FLOWBOT_PREFERRED_NAME = av.avatar;
    selected_avatar.FLOWBOT_AVATAR_ICON = av.icon;
    selected_avatar.FLOWBOT_AVATAR_DEMEANOR = av.demeanor;
    selected_avatar.FLOWBOT_AVATAR_PERSONA = av.persona;
    console.log(`[Avatar Applied] ${av.avatar} → persona: ${av.persona}`);
  }

  // 🧠 Connect with selected avatar
  function connectWithAvatar() {
    const avatarName = selected_avatar.FLOWBOT_PREFERRED_NAME;
    ConnectionManager.disconnect(); // ✅ Close any existing connection
    ConnectionManager.connect(sessionId, avatarName);
    console.log(`[WS] Connecting with avatar: ${avatarName}`);
  }

  // 🧠 Resolve initial avatar and connect
  const savedAvatarName = SessionManager.getCookie("selectedAvatar");
  const initialAvatar = siteProps.ALTERNATE_AVATARS.find(a => a.avatar === savedAvatarName)
    || siteProps.ALTERNATE_AVATARS.find(a => a.default)
    || siteProps.ALTERNATE_AVATARS[0];

  applyAvatarSelection(initialAvatar);
  updateSelectedUI();
  setTimeout(connectWithAvatar, 100); // ✅ Delay avoids race with UI init

  // 🧠 Populate dropdown
  siteProps.ALTERNATE_AVATARS.forEach(av => {
    const item = document.createElement("div");
    item.className = "dropdown-item";
    item.innerHTML = `<img src="${av.icon}" alt="${av.avatar}"><span>${av.avatar} — ${av.persona}</span>`;
    item.addEventListener("click", () => {
      const oldName = selected_avatar.FLOWBOT_PREFERRED_NAME;
      applyAvatarSelection(av);
      SessionManager.setCookie("selectedAvatar", av.avatar, 365);
      updateSelectedUI();
      dropdown.classList.remove("open");
      addSystemMessage(`(${oldName} helper now changed to ${selected_avatar.FLOWBOT_PREFERRED_NAME}...)`);
      connectWithAvatar(); // ✅ Reconnect with new avatar
    });
    dropdownList.appendChild(item);
  });

  // 🧠 Support email button
  if (siteProps.SUPPORT_EMAIL) {
    supportBtn.textContent = "Email PermitFlow Support";
    supportBtn.style.display = "inline-block";
    supportBtn.addEventListener("click", () => {
      window.location.href = `mailto:${siteProps.SUPPORT_EMAIL}`;
    });
  }

  // 🧠 Send message handler
  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    ConnectionManager.addMessageFn(text, "user");
    input.value = "";

    const avatarName = selected_avatar.FLOWBOT_PREFERRED_NAME;

    if (!ConnectionManager.isConnected()) {
      console.warn("Disconnected. Message queued.");
      fetch(`/send?session=${sessionId}&avatar=${avatarName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
    } else {
      ConnectionManager.ws.send(text);
    }
  }

  // 🧠 Event listeners for sending messages
  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
}