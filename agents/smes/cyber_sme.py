from langchain.tools import Tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_config import get_llm, PROMPTS

class CyberSMEOutputParser(JsonOutputParser):
    def parse(self, text: str):
        print("\n[DEBUG] Raw LLM output from CyberSME:\n", text)
        try:
            parsed = super().parse(text)
            print("\n[DEBUG] Parsed SME decision:\n", parsed)
            return parsed
        except Exception as e:
            print(f"[DEBUG] JSON parse error: {e}")
            return {
                "decision": "error",
                "justification": "Invalid JSON",
                "confidence": 0.0
            }

def get_cyber_sme_tool():
    """
    Returns a LangChain Tool that evaluates permit applications for cybersecurity risks.
    Accepts a single string containing the application details.
    """
    llm = get_llm(temperature=0)
    prompt = PROMPTS["cyber_sme"]

    def run(application_str: str):
        # Debug: show what we're sending to the LLM
        print("\n[DEBUG] Sending application to CyberSME:\n", application_str)
        chain = prompt | llm | CyberSMEOutputParser()
        return chain.invoke({"application": application_str})

    return Tool(
        name="CyberSME",
        func=run,
        description="Evaluates permit applications for cybersecurity risks and returns a JSON decision."
    )