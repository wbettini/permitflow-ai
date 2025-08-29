class FlowBot:
    def __init__(self, state_manager, required_fields):
        self.state = state_manager
        self.required_fields = required_fields

    def start(self, permit_type: str):
        self.state.set("permit_type", permit_type)
        self.state.set("application", {})
        return f"Welcome to PermitFlow-AI! Let's start your {permit_type} application."

    def next_step(self, user_input: dict) -> dict:
        # Merge new input into application state
        app_data = self.state.get("application", {})
        app_data.update(user_input)
        self.state.set("application", app_data)

        # Find missing fields
        missing = [f for f in self.required_fields if f not in app_data or not app_data[f]]

        if missing:
            return {
                "status": "incomplete",
                "message": f"I still need: {', '.join(missing)}",
                "application_so_far": app_data
            }
        else:
            return {
                "status": "complete",
                "message": "All required info collected. Moving to SME review...",
                "application": app_data
            }