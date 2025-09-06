import json
from pathlib import Path
from langchain_config import get_llm, flowbot_conversational_prompt
from agents.smes.cyber_sme import get_cyber_sme_tool
from agents.smes.infra_sme import get_infra_sme_tool

class FlowBot:
    def __init__(self, state_manager, required_fields, prompts_file="permitFlowDb/tollgate_prompts.json"):
        self.state = state_manager
        self.required_fields = required_fields
        self.llm = get_llm(temperature=0.7)
        self.history = []
        self.current_tollgate = 1
        self.current_prompt_index = 1  # Track which prompt within the tollgate we're on
        self.prompts = self._load_prompts(prompts_file)

    def _load_prompts(self, file_path):
        with open(Path(file_path), "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_prompt(self, tollgate_number, prompt_number):
        return self.prompts.get(str(tollgate_number), {}).get(str(prompt_number), "")

    def _get_total_prompts(self, tollgate_number):
        return len(self.prompts.get(str(tollgate_number), {}))

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

        # If there are more prompts left in the current tollgate, deliver the next one
        if self.current_prompt_index < self._get_total_prompts(self.current_tollgate):
            self.current_prompt_index += 1
            prompt_text = self._get_prompt(self.current_tollgate, self.current_prompt_index)
            self.history.append(("FlowBot", prompt_text))
            return prompt_text

        # Otherwise, proceed with normal logic
        app_data = self.state.get("application", {})
        if ":" in user_message:
            field, value = [p.strip() for p in user_message.split(":", 1)]
            app_data[field] = value
            self.state.set("application", app_data)

        missing = [f for f in self.required_fields if f not in app_data or not app_data[f]]

        if self.current_tollgate == 1:
            if missing:
                return self._ask_for_missing_field(missing, app_data)
            else:
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

    def _ask_for_missing_field(self, missing, app_data):
        prompt = flowbot_conversational_prompt()
        next_question = f"Could you tell me the {missing[0]}?"
        response = (prompt | self.llm).invoke({
            "history": self.format_history(),
            "missing_fields": ", ".join(missing),
            "application": app_data,
            "next_question": next_question
        })
        self.history.append(("FlowBot", response))
        return response

    def format_history(self):
        return "\n".join(f"{speaker}: {msg}" for speaker, msg in self.history)

    def run_sme_reviews(self, application: dict) -> dict:
        app_str = "\n".join(f"{k}: {v}" for k, v in application.items())
        print("\n[DEBUG] Sending application to CyberSME:\n", app_str)
        cyber_result = get_cyber_sme_tool().run(app_str)
        print("\n[DEBUG] Sending application to InfraSME:\n", app_str)
        infra_result = get_infra_sme_tool().run(app_str)
        return {"CyberSME": cyber_result, "InfraSME": infra_result}

    def aggregate_decisions(self, sme_results: dict) -> tuple[str, str]:
        # Weighted + debug logic from earlier version
        cyber = sme_results.get("CyberSME", {})
        infra = sme_results.get("InfraSME", {})
        cyber_decision = cyber.get("decision", "").lower()
        cyber_conf = cyber.get("confidence", 0.0)
        cyber_just = cyber.get("justification", "")
        infra_decision = infra.get("decision", "").lower()
        infra_conf = infra.get("confidence", 0.0)
        infra_just = infra.get("justification", "")

        print("\n[DEBUG] --- SME Decisions ---")
        print(f"CyberSME: decision={cyber_decision}, confidence={cyber_conf}, justification={cyber_just}")
        print(f"InfraSME: decision={infra_decision}, confidence={infra_conf}, justification={infra_just}")

        if cyber_decision == "decline" and cyber_conf >= 0.8:
            print("[DEBUG] CyberSME veto triggered (confidence >= 0.8)")
            return ("decline", f"CyberSME vetoed:\n- {cyber_just}\n- InfraSME: {infra_just}")

        weights = {"CyberSME": 0.6, "InfraSME": 0.4}
        def score(decision, confidence, weight):
            return (1 if decision == "approve" else -1) * confidence * weight
        cyber_score = score(cyber_decision, cyber_conf, weights["CyberSME"])
        infra_score = score(infra_decision, infra_conf, weights["InfraSME"])
        total_score = cyber_score + infra_score

        print("\n[DEBUG] --- Weighted Scoring ---")
        print(f"CyberSME score: {cyber_score:.3f} (weight={weights['CyberSME']})")
        print(f"InfraSME score: {infra_score:.3f} (weight={weights['InfraSME']})")
        print(f"Total weighted score: {total_score:.3f}")

        if total_score >= 0:
            print("[DEBUG] Final decision: APPROVE (score >= 0)")
            return ("approve", f"Weighted SME consensus approval:\n- CyberSME: {cyber_just}\n- InfraSME: {infra_just}")
        else:
            print("[DEBUG] Final decision: DECLINE (score < 0)")
            return ("decline", f"Weighted SME consensus decline:\n- CyberSME: {cyber_just}\n- InfraSME: {infra_just}")

    def format_final_output(self, application, sme_results, final_decision, final_justification):
        return f"""
Permit to Design Application Summary
------------------------------------
Permit Type: {self.state.get("permit_type")}
Application Data:
{application}

SME Results:
{sme_results}

Final Decision: {final_decision.upper()}
Justification:
{final_justification}
"""