class CyberSME:
    def review(self, application: dict) -> dict:
        decision = "approve" if application.get("owner") else "decline"
        justification = (
            "Controls documented and owner accountable."
            if decision == "approve"
            else "Missing owner; assign accountable owner and resubmit."
        )
        return {"role": "Cybersecurity", "decision": decision, "justification": justification}