class HumanReviewer:
    def review(self, consolidated: dict) -> dict:
        # Placeholder: In real life, this would be a manual approval step
        # For demo purposes, we just echo the decision and mark it as "reviewed"
        return {
            "human_reviewer": "Pending manual sign-off",
            "final_decision": consolidated["final_decision"],
            "justifications": consolidated["justifications"]
        }