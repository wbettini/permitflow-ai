# permitflow-ai
Agentic, multi‑role tollgate approvals — featuring FlowBot orchestration and human‑in‑the‑loop review.



uvicorn main:app --reload --host 0.0.0.0 --port 8000
- http://localhost:8000/health → should return {"status":"ok"}.
- http://localhost:8000/docs → interactive Swagger UI.
https://vigilant-acorn-qx7r9744qhxp4-8000.app.github.dev/health
https://vigilant-acorn-qx7r9744qhxp4-8000.app.github.dev/docs

curl -s -X POST http://localhost:8000/permit/run \
  -H "Content-Type: application/json" \
  -d '{"permit_type":"Permit to Design","application":{"name":"Sample App","owner":"Demo User"}}' | jq