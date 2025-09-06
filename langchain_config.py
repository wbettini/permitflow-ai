# langchain_config.py
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# Load environment variables from .env
load_dotenv()

try:
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI  # fallback for older LC versions
    AzureChatOpenAI = None

# -------------------------
# Default timeout for all LLM calls (seconds)
# -------------------------
DEFAULT_LLM_TIMEOUT = 15

# -------------------------
# Lazy-loaded LLM instance
# -------------------------
_llm_instance = None  # private cache

def get_llm(temperature: float = 0.2, model: str | None = None, streaming: bool = False):
    """
    Returns a LangChain-compatible LLM based on LLM_PROVIDER in .env.
    Lazily initializes the LLM on first call to reduce startup time and memory usage.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    provider = (os.getenv("LLM_PROVIDER") or "openai").lower()

    if provider == "openai":
        model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"⚡ Initializing OpenAI LLM: {model_name}")
        _llm_instance = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            streaming=streaming,
            request_timeout=DEFAULT_LLM_TIMEOUT
        )
        return _llm_instance

    if provider == "azure_openai":
        if AzureChatOpenAI is None:
            raise RuntimeError("langchain-openai package not installed")
        print(f"⚡ Initializing Azure OpenAI LLM: {model or os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
        _llm_instance = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_deployment=model or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            temperature=temperature,
            streaming=streaming,
            request_timeout=DEFAULT_LLM_TIMEOUT
        )
        return _llm_instance

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

# -------------------------
# Memory
# -------------------------
def get_memory(session_id: str | None = None):
    """
    Returns a simple in-memory conversation buffer.
    Replace with persistent storage for multi-user deployments.
    """
    return ConversationBufferMemory(
        memory_key="history",
        input_key="input",
        return_messages=True
    )

# ---------- Prompt Templates ----------
def flowbot_system_prompt() -> str:
    return (
        "You are FlowBot, the orchestrator agent inside the PermitFlow application. "
        "You guide applicants through the tollgate approval process, gather missing information, "
        "and call SME tools (Cyber, Infra, Finance) when needed. "
        "Always explain decisions clearly and maintain a helpful, professional tone."
    )

def cyber_sme_prompt_template() -> PromptTemplate:
    template = """
You are a Cybersecurity SME evaluating a permit application.

Application details:
{application}

Return a strict JSON object with keys:
- decision: "approve" or "decline"
- justification: short, concrete rationale mentioning key risk factors
- confidence: a float between 0 and 1

JSON only. No extra text.
"""
    return PromptTemplate(input_variables=["application"], template=template.strip())

PROMPTS = {
    "cyber_sme": cyber_sme_prompt_template(),
}

def flowbot_conversational_prompt():
    return PromptTemplate(
        input_variables=["history", "missing_fields", "application", "next_question"],
        template="""
You are FlowBot, a friendly and knowledgeable guide for the Permit to Design process.
You help applicants step-by-step, explaining tollgates and collecting required information.

Conversation so far:
{history}

Current application data:
{application}

Missing fields:
{missing_fields}

Your task:
- If there are missing fields, ask for them conversationally, one at a time.
- If no fields are missing, explain that you'll proceed to SME review.
- Keep responses warm, clear, and professional.

Next question to ask:
{next_question}
"""
    )