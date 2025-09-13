export const SessionManager = {
  setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${value};expires=${expires};path=/`;
  },
  getCookie(name) {
    const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
    return match ? match[2] : null;
  },
  getSessionId() {
    let sessionId = this.getCookie("flowbotSessionId");
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      this.setCookie("flowbotSessionId", sessionId, 7);
    }
    return sessionId;
  }
};

export const sessionId = SessionManager.getSessionId();