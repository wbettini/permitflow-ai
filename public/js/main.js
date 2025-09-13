import { sessionId } from './session.js';
import { loadSiteProperties } from './config.js';
import { ConnectionManager } from './connection.js';
import { addMessage, updateStatus } from './ui.js';
import { initUI } from './events.js';

document.addEventListener("DOMContentLoaded", async () => {
  // 1️⃣ Load site properties
  const siteProps = await loadSiteProperties();

  // 2️⃣ Initialize UI (dropdown, avatar selection, event listeners)
  initUI(siteProps, sessionId, ConnectionManager);

  // 3️⃣ Inject UI hooks into ConnectionManager
  ConnectionManager.addMessageFn = addMessage;
  ConnectionManager.updateStatusFn = (text, color) => updateStatus(text, color, sessionId);

  // 4️⃣ Mark UI as ready and flush any queued bot messages
  ConnectionManager.uiReady = true;
  ConnectionManager.flushQueue();

  // ✅ No direct connect here — events.js will handle it after avatar resolution
});