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
- Configurable via `tollgates.yaml` — no code changes required to add/remove SMEs.

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
   uvicorn main:app --reload --host 0.0.0.0 --port 8000

📈 Roadmap
- [ ] Add more SME agent types with domain‑specific logic.
- [ ] Integrate real human approval workflow.
- [ ] Persist application state in a database.
- [ ] Add authentication for SME and reviewer dashboards.
- [ ] Enhance UI with richer chat features and branding.

📜 
License MIT License — see LICENSE for details.


uvicorn main:app --reload --host 0.0.0.0 --port 8000
- http://localhost:8000/health → should return {"status":"ok"}.
- http://localhost:8000/docs → interactive Swagger UI.
https://vigilant-acorn-qx7r9744qhxp4-8000.app.github.dev/health
https://vigilant-acorn-qx7r9744qhxp4-8000.app.github.dev/docs

curl -s -X POST http://localhost:8000/permit/run \
  -H "Content-Type: application/json" \
  -d '{"permit_type":"Permit to Design","application":{"name":"Sample App","owner":"Demo User"}}' | jq