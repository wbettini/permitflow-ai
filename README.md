# 🚦 PermitFlow‑AI

**Agentic, multi‑role tollgate approvals — featuring FlowBot orchestration and human‑in‑the‑loop review.**

PermitFlow‑AI is an open‑source framework for orchestrating structured, multi‑stage approval workflows.  
Powered by **FlowBot**, your AI process navigator, it guides applicants step‑by‑step, collects SME (Subject Matter Expert) reviews with justifications, and ensures every outcome gets final human sign‑off — blending automation speed with accountability and transparency.

---

## ✨ Core Concepts

### **FlowBot — The Navigator**
- Greets and guides applicants through the permit process.
- Dynamically requests missing information.
- Routes applications to the correct SMEs based on permit type.
- Keeps state during the conversation so the process feels continuous.

### **SME Agents**
- Domain‑specific reviewers (e.g., Cybersecurity, Infrastructure, Finance).
- Each SME returns a decision (`approve` / `decline`) and a justification.
- Configurable via `app/core/tollgates.yaml` — no code changes required to add/remove SMEs.

### **Human‑in‑the‑Loop**
- Final review stage for accountability.
- Placeholder in the demo; can be integrated with real approval systems.

### **Azure‑Friendly Architecture**
- Stateless FastAPI backend — runs identically in Codespaces and Azure Web Apps.
- WebSocket endpoint for real‑time chat.
- Lightweight HTML/JS front‑end served from `/` for instant browser access.

---

## 🗂 Project Structure
permitflow-ai/ ├── agents/ │   ├── flowbot/flowbot.py       # FlowBot navigator logic │   └── smes/cyber_sme.py        # Example SME agent ├── core/ │   ├── orchestration.py         # Orchestrates FlowBot, SMEs, and human review │   ├── state_manager.py         # In-memory state tracking │   ├── human_review.py          # Human-in-the-loop placeholder │   └── config_loader.py         # Loads tollgate config from YAML ├── public/ │   ├── index.html               # Chat UI │   ├── flowbot-avatar.png       # FlowBot branding │   └── user-avatar.png          # User avatar ├── tollgates.yaml               # Permit types, required fields, SME mapping ├── main.py                      # FastAPI entrypoint ├── requirements.txt └── README.md


---

## 🚀 Quick Start (Codespaces)

1. **Open in Codespaces**  
   Click the green **Code** button → **Codespaces** tab → **Create codespace on main**.

2. **Run the app**  
   ```bash
   gunicorn -c gunicorn_conf.py app.main:app

📈 Roadmap
- [ ] Add more SME agent types with domain‑specific logic.
- [ ] Integrate real human approval workflow.
- [ ] Persist application state in a database.
- [ ] Add authentication for SME and reviewer dashboards.
- [ ] Enhance UI with richer chat features and branding.

📜 
License MIT License — see LICENSE for details.


🤝 Contributing
Pull requests are welcome!
If you have ideas for new SME agents, UI improvements, or integrations, open an issue or fork the repo.💡 Why PermitFlow‑AI?Most approval workflows are slow, opaque, and siloed.
PermitFlow‑AI makes them:- Transparent — every decision has a justification.
- Efficient — FlowBot collects exactly what’s needed, no more, no less.
- Flexible — easily reconfigure SMEs and required fields without code changes.
- Engaging — real‑time chat makes the process feel human, not bureaucratic.

---

## Live Status

<p align="center">
  <img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/wbettini/93c19d78e2f7ea5477c83cfa3bb5b2d3/raw/latency.json&cacheSeconds=60" alt="Avg Latency">
  <img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/wbettini/8902bf762ca4daa4a38e4e7b4b0c483f/raw/uptime.json&cacheSeconds=60" alt="Uptime">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/wbettini/permitflow-ai/main/monitoring/latency_trends.png" alt="Azure Smoke Test Latency Trends" width="700">
</p>

<p align="center"><em>Last updated: <!--LAST_UPDATED-->2026-01-21 02:48:42 UTC<!--LAST_UPDATED--></em></p>