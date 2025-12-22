from langchain.tools import Tool
from langchain_core.output_parsers import JsonOutputParser
from app.langchain_config import get_llm
from langchain.prompts import PromptTemplate

# Define the ArchitectureSME prompt template
architecture_prompt = PromptTemplate(
    input_variables=["application"],
    template="""
You are a Software Architecture SME evaluating a permit application.
Your goal is to ensure the proposed solution aligns with enterprise architecture standards, uses approved technology stacks, and follows best practices for scalability and maintainability.

Application details:
{application}

Return a strict JSON object with keys:
- decision: "approve" or "decline"
- justification: short, concrete rationale mentioning architectural patterns, tech stack, or scalability.
- confidence: a float between 0 and 1

JSON only. No extra text.
""".strip()
)


class ArchitectureSMEOutputParser(JsonOutputParser):
    def parse(self, text: str):
        print("\n[DEBUG] Raw LLM output from ArchitectureSME:\n", text)
        try:
            parsed = super().parse(text)
            print("\n[DEBUG] Parsed ArchitectureSME decision:\n", parsed)
            return parsed
        except Exception as e:
            print(f"[DEBUG] JSON parse error: {e}")
            return {
                "decision": "error",
                "justification": "Invalid JSON",
                "confidence": 0.0
            }


def get_architecture_sme_tool():
    llm = get_llm(temperature=0)

    def run(application_str: str):
        print("\n[DEBUG] Sending application to ArchitectureSME:\n",
              application_str)
        chain = architecture_prompt | llm | ArchitectureSMEOutputParser()
        return chain.invoke({"application": application_str})

    return Tool(
        name="ArchitectureSME",
        func=run,
        description="Evaluates permit applications for software architecture alignment and returns a JSON decision."
    )
