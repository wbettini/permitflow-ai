// ===== Cookie Helpers =====
function setCookie(name, value, days) {
  const d = new Date();
  d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = `${name}=${value};expires=${d.toUTCString()};path=/`;
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

// ===== Default site properties =====
const defaults = {
  FLOWBOT_PREFERRED_NAME: 'FlowBot',
  SUPPORT_EMAIL: 'support@permitflow.bettini.us',
  DEFAULT_LANGUAGE: 'en-US',
  ALTERNATE_AVATARS: [
    { avatar: 'FlowBot', demeanor: 'Chippy', icon: '/static/flowbot-avatar.png' }
  ]
};

// ===== Selected Avatar Object =====
let selected_avatar = {
  FLOWBOT_PREFERRED_NAME: defaults.FLOWBOT_PREFERRED_NAME,
  FLOWBOT_AVATAR_ICON: defaults.ALTERNATE_AVATARS[0].icon,
  FLOWBOT_AVATAR_DEMEANOR: defaults.ALTERNATE_AVATARS[0].demeanor
};

// ===== Connection State =====
let ws;
let eventSource;
let usingSSE = false;

document.addEventListener('DOMContentLoaded', () => {
  const heading = document.getElementById('chat-heading');
  const dropdown = document.getElementById('avatar-dropdown');
  const dropdownSelected = document.getElementById('dropdown-selected');
  const dropdownList = document.getElementById('dropdown-list');
  const selectedImg = dropdownSelected.querySelector('img');
  const selectedName = dropdownSelected.querySelector('.dropdown-name');
  const messagesDiv = document.getElementById('messages');
  const input = document.getElementById('input');
  const sendBtn = document.getElementById('send-btn');

  // Optional: connection status indicator
  const statusIndicator = document.createElement('div');
  statusIndicator.id = "connection-status";
  statusIndicator.style.fontSize = "0.8em";
  statusIndicator.style.marginBottom = "5px";
  messagesDiv.parentNode.insertBefore(statusIndicator, messagesDiv);

  // Toggle dropdown
  dropdownSelected.addEventListener('click', () => {
    dropdown.classList.toggle('open');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove('open');
    }
  });

  // Fetch site properties and merge with defaults
  fetch('/site-properties')
    .then(res => res.json())
    .then(data => {
      const props = { ...defaults, ...data };

      if (!Array.isArray(props.ALTERNATE_AVATARS) || props.ALTERNATE_AVATARS.length === 0) {
        props.ALTERNATE_AVATARS = defaults.ALTERNATE_AVATARS;
      }

      // Determine initial avatar from cookie or default to first
      const savedAvatarName = getCookie('selectedAvatar');
      let initial = props.ALTERNATE_AVATARS.find(a => a.avatar === savedAvatarName) || props.ALTERNATE_AVATARS[0];

      selected_avatar = {
        FLOWBOT_PREFERRED_NAME: initial.avatar,
        FLOWBOT_AVATAR_ICON: initial.icon,
        FLOWBOT_AVATAR_DEMEANOR: initial.demeanor
      };

      // Populate dropdown list
      props.ALTERNATE_AVATARS.forEach(av => {
        const item = document.createElement('div');
        item.className = 'dropdown-item';
        item.innerHTML = `<img src="${av.icon}" alt="${av.avatar}"><span>${av.avatar} — ${av.demeanor}</span>`;
        item.addEventListener('click', () => {
          const oldName = selected_avatar.FLOWBOT_PREFERRED_NAME;
          selected_avatar = {
            FLOWBOT_PREFERRED_NAME: av.avatar,
            FLOWBOT_AVATAR_ICON: av.icon,
            FLOWBOT_AVATAR_DEMEANOR: av.demeanor
          };
          setCookie('selectedAvatar', av.avatar, 365);
          updateSelectedUI();
          dropdown.classList.remove('open');
          addSystemMessage(`(${oldName} helper now changed to ${selected_avatar.FLOWBOT_PREFERRED_NAME}...)`);
        });
        dropdownList.appendChild(item);
      });

      // Initial UI update
      updateSelectedUI();

      // Support email button
      const btn = document.getElementById('support-email-btn');
      if (props.SUPPORT_EMAIL) {
        btn.textContent = `Email PermitFlow Support`;
        btn.style.display = 'inline-block';
        btn.addEventListener('click', () => {
          window.location.href = `mailto:${props.SUPPORT_EMAIL}`;
        });
      }

      // Start connection
      connectWebSocket();
    })
    .catch(err => {
      console.error('Error loading site properties:', err);
      updateSelectedUI();
    });

  // ===== Connection Logic =====
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(
      `${protocol}://${window.location.host}/ws/flowbot?avatar=${encodeURIComponent(selected_avatar.FLOWBOT_PREFERRED_NAME)}`
    );

    ws.onopen = () => {
      usingSSE = false;
      updateStatus("Connected via WebSocket", "green");
    };

    ws.onmessage = (event) => {
      addMessage(event.data, 'bot');
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
    eventSource = new EventSource("/events");

    eventSource.onopen = () => {
      updateStatus("Connected via SSE", "orange");
    };

    eventSource.onmessage = (event) => {
      addMessage(event.data, 'bot');
    };

    eventSource.onerror = () => {
      updateStatus("Disconnected", "red");
      eventSource.close();
    };
  }

  // ===== Send Message =====
  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    if (!usingSSE && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(text);
    } else {
      fetch("/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
    }
    addMessage(text, 'user');
    input.value = '';
  }

  // ===== UI Helpers =====
  function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${sender}`;

    const avatar = document.createElement('img');
    avatar.className = 'avatar';
    avatar.src = sender === 'bot'
      ? (selected_avatar.FLOWBOT_AVATAR_ICON || defaults.ALTERNATE_AVATARS[0].icon)
      : '/static/user-avatar.png';
    avatar.alt = sender === 'bot'
      ? selected_avatar.FLOWBOT_PREFERRED_NAME
      : 'You';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function addSystemMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'msg system';

    const bubble = document.createElement('div');
    bubble.className = 'bubble system-bubble';
    bubble.textContent = text;

    msgDiv.appendChild(bubble);
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  function updateSelectedUI() {
    heading.textContent = `💬 Chat with ${selected_avatar.FLOWBOT_PREFERRED_NAME}`;
    selectedImg.src = selected_avatar.FLOWBOT_AVATAR_ICON;
    selectedName.textContent = `${selected_avatar.FLOWBOT_PREFERRED_NAME} — ${selected_avatar.FLOWBOT_AVATAR_DEMEANOR}`;
    window.currentBotAvatar = selected_avatar.FLOWBOT_AVATAR_ICON;
  }

  function updateStatus(text, color) {
    statusIndicator.textContent = text;
    statusIndicator.style.color = color;
  }

  // ===== Event Listeners =====
  sendBtn.addEventListener("click", sendMessage);

  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
});