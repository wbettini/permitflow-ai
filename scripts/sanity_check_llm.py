# scripts/sanity_check_llm.py
"""
Quick test to verify Azure OpenAI connection using values from .env
Run with: python scripts/sanity_check_llm.py
"""

import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

try:
    from langchain_openai import AzureChatOpenAI
except ImportError:
    raise RuntimeError(
        "langchain-openai package not installed. Install with: pip install langchain-openai"
    )

def main():
    # Pull config from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    # Basic validation
    if not all([endpoint, api_key, deployment]):
        raise ValueError("Missing one or more required Azure OpenAI env vars in .env")

    # Create the LLM client
    llm = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        azure_deployment=deployment,
        api_version=api_version,
        temperature=0
    )

    # Send a test prompt
    print("Sending test prompt to Azure OpenAI...")
    response = llm.invoke("Say hello from Azure OpenAI in eastus2 for the PermitFlow project.")
    print("✅ Response from Azure OpenAI:")
    print(response.content)

if __name__ == "__main__":
    main()