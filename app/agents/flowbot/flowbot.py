import json
import re
from pathlib import Path
from langchain_config import get_llm, flowbot_conversational_prompt
from app.agents.smes.cyber_sme import get_cyber_sme_tool
from app.agents.smes.infra_sme import get_infra_sme_tool
from app.core.site_properties import get_site_property

class FlowBot:
    def __init__(self, state_manager, required_fields, prompts_file="permitFlowDb/tollgate_prompts.json"):
        self.state = state_manager
        self.required_fields = required_fields
        self.llm = None  # Lazy init
        self.history = []
        self.current_tollgate = 1
        self.current_prompt_index = 1
        self.prompts = self._load_prompts(Path(prompts_file))
        self.bot_name = get_site_property("FLOWBOT_PREFERRED_NAME", "FlowBot")

    # ─────────────────────────────────────────────────────────────
    # 🔧 Initialization & Prompt Loading
    # ─────────────────────────────────────────────────────────────
    def _ensure_llm(self):
        if self.llm is None:
            self.llm = get_llm(temperature=0.7)
        return self.llm

    def _load_prompts(self, prompts_file: Path):
        if not prompts_file.exists():
            raise FileNotFoundError(f"Prompts file not found: {prompts_file}")
        content = prompts_file.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError(f"Prompts file is empty: {prompts_file}")
        return json.loads(content)

    def _get_prompt(self, tollgate_number, prompt_number):
        return self.prompts.get(str(tollgate_number), {}).get(str(prompt_number), "")

    def _get_total_prompts(self, tollgate_number):
        return len(self.prompts.get(str(tollgate_number), {}))

    # ─────────────────────────────────────────────────────────────
    # 🧠 Field Extraction from User Input
    # ─────────────────────────────────────────────────────────────
    def _extract_field_from_text(self, text):
        patterns = {
            "service_name": r"(?:called|named|service name (?:is|will be)|project is|project will be)\s+([A-Za-z0-9 _-]+)",
            "owner": r"(?:I am|I will be|owned by|owner is)\s+([A-Za-z0-9 _-]+)",
            "data_classification": r"(Confidential|Public|Internal|Sensitive|Not sensitive|Non[- ]?private|Non[- ]?sensitive)"
        }
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return field, match.group(1).strip()
        return None, None

    # ─────────────────────────────────────────────────────────────
    # 💬 Conversation Flow
    # ─────────────────────────────────────────────────────────────
    def start(self, permit_type: str):
        self.state.set("permit_type", permit_type)
        self.state.set("application", {})
        self.current_tollgate = 1
        self.current_prompt_index = 1
        greeting = self._get_prompt(1, 1)
        self.history.append(("FlowBot", greeting))
        return greeting

    def converse(self, user_message: str) -> str:
        self.history.append(("User", user_message))
        app_data = self.state.get("application", {})

        # ── Prompt progression ──
        if self.current_prompt_index < self._get_total_prompts(self.current_tollgate):
            self.current_prompt_index += 1
            prompt_text = self._get_prompt(self.current_tollgate, self.current_prompt_index)
            self.history.append(("FlowBot", prompt_text))
            return prompt_text

        # ── Field extraction ──
        field, value = self._extract_field_from_text(user_message)
        if field and value:
            app_data[field] = value
        elif ":" in user_message:
            field, value = [p.strip() for p in user_message.split(":", 1)]
            app_data[field] = value
        self.state.set("application", app_data)

        # ── Tollgate logic ──
        missing = [f for f in self.required_fields if f not in app_data or not app_data[f]]

        if self.current_tollgate == 1:
            if missing:
                return self._ask_for_missing_field(missing, app_data)
            self.current_tollgate = 2
            self.current_prompt_index = 1
            return self._get_prompt(2, 1)

        if self.current_tollgate == 2:
            sme_results = self.run_sme_reviews(app_data)
            self.current_tollgate = 3
            self.current_prompt_index = 1
            return self._get_prompt(3, 1) + "\n" + self.format_final_output(
                app_data, sme_results, *self.aggregate_decisions(sme_results)
            )

        if self.current_tollgate == 3:
            return "✅ Process complete. Start a new application to begin again."

        # ── Fallback: LLM-powered reply ──
        llm = self._ensure_llm()
        prompt = flowbot_conversational_prompt()
        raw_response = (prompt | llm).invoke({
            "history": self.format_history(),
            "application": "\n".join(f"{k}: {v}" for k, v in app_data.items()),
            "next_question": user_message
        })
        response = str(raw_response)
        self.history.append(("FlowBot", response))
        return response

    def _ask_for_missing_field(self, missing, app_data):
        current_field = missing[0]
        next_question = f"Could you tell me the {current_field}?"
        llm = self._ensure_llm()
        prompt = flowbot_conversational_prompt()
        raw_response = (prompt | llm).invoke({
            "history": self.format_history(),
            "missing_fields": ", ".join(missing),
            "application": "\n".join(f"{k}: {v}" for k, v in app_data.items()),
            "next_question": next_question
        })
        response = str(raw_response)
        self.history.append(("FlowBot", response))
        return response

    def format_history(self):
        return "\n".join(f"{speaker}: {msg}" for speaker, msg in self.history)

    # ─────────────────────────────────────────────────────────────
    # 🧪 SME Orchestration
    # ─────────────────────────────────────────────────────────────
    def run_sme_reviews(self, application: dict) -> dict:
        app_str = "\n".join(f"{k}: {v}" for k, v in application.items())
        results = {}

        # Cyber SME
        try:
            cyber_tool = get_cyber_sme_tool()
            if hasattr(cyber_tool, "llm") and hasattr(cyber_tool.llm, "request_timeout"):
                cyber_tool.llm.request_timeout = 15
            results["CyberSME"] = cyber_tool.run(app_str)
        except Exception as e:
            results["CyberSME"] = {
                "decision": "error",
                "justification": f"CyberSME error: {e}",
                "confidence": 0.0
            }

        # Infra SME
        try:
            infra_tool = get_infra_sme_tool()
            if hasattr(infra_tool, "llm") and hasattr(infra_tool.llm, "request_timeout"):
                infra_tool.llm.request_timeout = 15
            results["InfraSME"] = infra_tool.run(app_str)
        except Exception as e:
            results["InfraSME"] = {
                "decision": "error",
                "justification": f"InfraSME error: {e}",
                "confidence": 0.0
            }

        return results

    # ─────────────────────────────────────────────────────────────
    # 📊 Decision Aggregation
    # ─────────────────────────────────────────────────────────────
    def aggregate_decisions(self, sme_results: dict) -> tuple[str, str]:
        def score(decision, confidence, weight):
            return (1 if decision == "approve" else -1) * confidence * weight

        cyber = sme_results.get("CyberSME", {})
        infra = sme_results.get("InfraSME", {})
        cyber_score = score(cyber.get("decision", "").lower(), cyber.get("confidence", 0.0), 0.6)
        infra_score = score(infra.get("decision", "").lower(), infra.get("confidence", 0.0), 0.4)
        total_score = cyber_score + infra_score

        if cyber.get("decision") == "decline" and cyber.get("confidence", 0.0) >= 0.8:
            return ("decline", f"CyberSME vetoed:\n- {cyber.get('justification')}\n- InfraSME: {infra.get('justification')}")

        if total_score >= 0:
            return (
                "approve",
                f"Weighted SME consensus approval:\n- CyberSME: {cyber.get('justification')}\n- InfraSME: {infra.get('justification')}"
            )
        else:
            return (
                "decline",
                f"Weighted SME consensus decline:\n- CyberSME: {cyber.get('justification')}\n- InfraSME: {infra.get('justification')}"
            )