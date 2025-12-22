from app.agents.flowbot.flowbot import FlowBot
import sys
import asyncio
from pathlib import Path

# --- Ensure project root is in sys.path ---
sys.path.append(str(Path(__file__).resolve().parent.parent))


async def main():
    # Create FlowBot
    user_id = "test_user_123"
    bot = FlowBot(user_id=user_id)

    print("FlowBot initialized. Type 'quit' to exit.")

    # Simple REPL loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"quit", "exit"}:
                print("Exiting FlowBot conversation.")
                break

            response = await bot.handle_message(user_input)
            print(f"\nFlowBot: {response}")

        except KeyboardInterrupt:
            print("\nExiting FlowBot conversation.")
            break

if __name__ == "__main__":
    asyncio.run(main())
