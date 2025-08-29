from core.state_manager import StateManager
from agents.flowbot.flowbot import FlowBot
from agents.smes.cyber_sme import CyberSME
from core.human_review import HumanReviewer
from core.config_loader import load_tollgate_config

class Orchestrator:
    def __init__(self):
        self.state = StateManager()
        self.config = load_tollgate_config()
        self.flowbot = None
        self.smes = []
        self.human_reviewer = HumanReviewer()

    def start_permit(self, permit_type: str):
        cfg = self.config.get(permit_type)
        if not cfg:
            return {"error": f"Unknown permit type: {permit_type}"}
        self.flowbot = FlowBot(self.state, cfg["required_fields"])
        self.smes = [CyberSME()]  # Later: map SME names to classes dynamically
        return {"message": self.flowbot.start(permit_type)}

    def continue_permit(self, user_input: dict):
        step = self.flowbot.next_step(user_input)
        if step["status"] == "complete":
            return self._run_sme_and_human_review(step["application"])
        return step

    def _run_sme_and_human_review(self, application: dict):
        decisions = [sme.review(application) for sme in self.smes]
        final = "approve" if all(d["decision"] == "approve" for d in decisions) else "decline"
        consolidated = {
            "final_decision": final,
            "justifications": [d["justification"] for d in decisions]
        }
        human_stage = self.human_reviewer.review(consolidated)
        return {
            "status": "finished",
            "decisions": decisions,
            "consolidated": consolidated,
            "human_review": human_stage
        }