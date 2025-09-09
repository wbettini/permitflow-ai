# agents/smes/infra_sme.py
from langchain.tools import Tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_config import get_llm, PROMPTS
from langchain.prompts import PromptTemplate

# Define the InfraSME prompt template
infra_prompt = PromptTemplate(
    input_variables=["application"],
    template="""
You are an Infrastructure SME evaluating a permit application.

Application details:
{application}

Return a strict JSON object with keys:
- decision: "approve" or "decline"
- justification: short, concrete rationale mentioning key infrastructure or operational factors
- confidence: a float between 0 and 1

JSON only. No extra text.
""".strip()
)

class InfraSMEOutputParser(JsonOutputParser):
    def parse(self, text: str):
        print("\n[DEBUG] Raw LLM output from InfraSME:\n", text)
        try:
            parsed = super().parse(text)
            print("\n[DEBUG] Parsed InfraSME decision:\n", parsed)
            return parsed
        except Exception as e:
            print(f"[DEBUG] JSON parse error: {e}")
            return {
                "decision": "error",
                "justification": "Invalid JSON",
                "confidence": 0.0
            }

def get_infra_sme_tool():
    llm = get_llm(temperature=0)

    def run(application_str: str):
        print("\n[DEBUG] Sending application to InfraSME:\n", application_str)
        chain = infra_prompt | llm | InfraSMEOutputParser()
        return chain.invoke({"application": application_str})

    return Tool(
        name="InfraSME",
        func=run,
        description="Evaluates permit applications for infrastructure and operational risks, returns a JSON decision."
    )