from core.state_manager import StateManager
from agents.flowbot.flowbot import FlowBot
from agents.smes.cyber_sme import CyberSME

class Orchestrator:
    def __init__(self):
        self.state = StateManager()
        self.flowbot = FlowBot(self.state)
        self.smes = [CyberSME()]

    def run(self, permit_type: str, application: dict) -> dict:
        intro = self.flowbot.start(permit_type, application)
        decisions = [sme.review(application) for sme in self.smes]
        final = "approve" if all(d["decision"] == "approve" for d in decisions) else "decline"
        return {
            "intro": intro,
            "decisions": decisions,
            "consolidated": {
                "final_decision": final,
                "justifications": [d["justification"] for d in decisions]
            }
        }