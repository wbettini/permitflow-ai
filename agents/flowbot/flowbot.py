class FlowBot:
    def __init__(self, state_manager):
        self.state = state_manager

    def start(self, permit_type: str, application: dict) -> str:
        fields = ", ".join(sorted(application.keys()))
        return f"FlowBot: Initialized for {permit_type}. Collected fields: {fields}"