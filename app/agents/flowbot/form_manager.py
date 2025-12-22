import json
from typing import Optional, Dict, Any, List
from app.services.application_service import ApplicationService
from app.langchain_config import get_llm
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.logger import logger

# Define required fields for Permit to Build
REQUIRED_FIELDS = {
    "project_name": "What is the name of your project?",
    "description": "Please provide a brief description of the project.",
    "tech_stack": "What is the proposed technology stack?",
    "compliance_level": "What is the compliance level (High, Medium, Low)?",
    "budget": "What is the estimated budget?"
}

extraction_prompt = PromptTemplate(
    input_variables=["history", "message", "missing_fields"],
    template="""
You are helping a user fill out a permit application.
Current missing fields: {missing_fields}

Conversation History:
{history}

User Message:
{message}

Extract values for any of the missing fields from the user's message.
Return a JSON object with the extracted keys and values.
If a value is not found, do not include the key.
If the user is trying to cancel or stop, return {{"intent": "cancel"}}.
If the user confirms submission (e.g. "yes", "submit"), return {{"intent": "submit"}}.

JSON only:
"""
)


class FormManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.app_service = ApplicationService()
        self.llm = get_llm(temperature=0)

    def handle_message(self, message: str, history: str) -> Optional[str]:
        """
        Returns a response string if the form manager handled the message.
        Returns None if the message should be handled by the normal FlowBot intent matcher.
        """
        app = self.app_service.get_active_application_by_session(self.user_id)

        # If no active app, check if user wants to start one (simple keyword check for now, or rely on FlowBot to call create)
        # Actually, FlowBot should detect "start permit" intent and call create_application.
        # So here we only handle if app exists.

        if not app:
            return None

        if app.status == "submitted":
            return "Your application is currently under review. We will notify you when a decision is made."

        # Determine missing fields
        current_data = app.data or {}
        missing = [f for f in REQUIRED_FIELDS if f not in current_data]

        if not missing:
            # All fields present, waiting for submission confirmation
            if "submit" in message.lower() or "yes" in message.lower():
                self.app_service.submit_application(app.id)
                # Trigger SMEs here or return a message saying it's started
                # For now, just return message. The Orchestrator/Service should handle the async trigger.
                return self._trigger_reviews(app.id)
            else:
                return "All fields are collected. Ready to submit? (Yes/No)"

        # Extract data
        extracted = self._extract_data(message, history, missing)

        if extracted.get("intent") == "cancel":
            # TODO: Cancel application
            return "Application cancelled."

        if extracted.get("intent") == "submit" and not missing:
            self.app_service.submit_application(app.id)
            return self._trigger_reviews(app.id)

        # Update DB with extracted fields
        # Filter out 'intent' key
        fields_to_update = {k: v for k, v in extracted.items() if k in missing}

        if fields_to_update:
            self.app_service.update_application_data(app.id, fields_to_update)
            # Recalculate missing
            missing = [
                f for f in REQUIRED_FIELDS if f not in current_data and f not in fields_to_update]

        if not missing:
            return f"Great! I have all the details:\n{self._format_summary(app.id)}\n\nReady to submit?"

        # Ask for next missing field
        next_field = missing[0]
        return REQUIRED_FIELDS[next_field]

    def start_application(self, permit_type: str) -> str:
        self.app_service.create_application(self.user_id, permit_type)
        return f"Starting a new {permit_type} application. " + REQUIRED_FIELDS["project_name"]

    def _extract_data(self, message: str, history: str, missing: List[str]) -> Dict[str, Any]:
        chain = extraction_prompt | self.llm | JsonOutputParser()
        try:
            return chain.invoke({
                "history": history,
                "message": message,
                "missing_fields": ", ".join(missing)
            })
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {}

    def _format_summary(self, app_id: int) -> str:
        app = self.app_service.get_application(app_id)
        data = app.data
        return "\n".join([f"- {k}: {v}" for k, v in data.items()])

    def _trigger_reviews(self, app_id: int) -> str:
        # This is where we call the SMEs
        # In a real app, this might be a background task
        from app.agents.smes.cyber_sme import get_cyber_sme_tool
        from app.agents.smes.architecture_sme import get_architecture_sme_tool

        app = self.app_service.get_application(app_id)
        app_str = json.dumps(app.data)

        results = []

        # Cyber SME
        cyber = get_cyber_sme_tool()
        cyber_result = cyber.run(app_str)
        self.app_service.add_review(app_id, "cyber", cyber_result.get(
            "decision"), cyber_result.get("justification"))
        results.append(f"Cybersecurity: {cyber_result.get('decision')}")

        # Architecture SME
        arch = get_architecture_sme_tool()
        arch_result = arch.run(app_str)
        self.app_service.add_review(app_id, "architecture", arch_result.get(
            "decision"), arch_result.get("justification"))
        results.append(f"Architecture: {arch_result.get('decision')}")

        # Check if all approved
        if all(r.get("decision") == "approve" for r in [cyber_result, arch_result]):
            self.app_service.log_event(app_id, "human_review_ready", {})
            return "SME Reviews Complete. All approved! Application is now ready for Human Review.\n" + "\n".join(results)
        else:
            return "SME Reviews Complete. Issues found:\n" + "\n".join(results)
