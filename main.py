from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any
from core.orchestration import Orchestrator

app = FastAPI(title="PermitFlow-AI", version="0.1.0")
orchestrator = Orchestrator()

class PermitRequest(BaseModel):
    permit_type: str = Field(..., examples=["Permit to Design"])
    application: Dict[str, Any] = Field(..., examples=[{"name": "Sample App", "owner": "Demo User"}])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/permit/run")
def run_permit(req: PermitRequest):
    result = orchestrator.run(req.permit_type, req.application)
    return result