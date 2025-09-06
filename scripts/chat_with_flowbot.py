import sys
from pathlib import Path

# --- Ensure project root is in sys.path ---
# This makes imports work no matter where you run the script from
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.state_manager import StateManager
from agents.flowbot.flowbot import FlowBot

# Define the required fields for the application
required_fields = ["service_name", "owner", "data_classification"]

def main():
    # Create StateManager and FlowBot
    state = StateManager()
    bot = FlowBot(state, required_fields, prompts_file="permitFlowDb/tollgate_prompts.json")

    # Start the conversation
    print(bot.start("cloud service permit"))

    # Simple REPL loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"quit", "exit"}:
                print("Exiting FlowBot conversation.")
                break

            response = bot.converse(user_input)
            print(f"\nFlowBot: {response}")

        except KeyboardInterrupt:
            print("\nExiting FlowBot conversation.")
            break

if __name__ == "__main__":
    main()