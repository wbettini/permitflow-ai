"""
🧪 flowbot_test.py — Manual test for FlowBot persona responses.

Run from project root or with PYTHONPATH set so /app is importable.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.agents.flowbot.flowbot import FlowBot

if __name__ == "__main__":
    test_message = "This is something random"

    for avatar in ["Alexandra", "Robert", "Emily", "FlowBot", "default"]:
        bot = FlowBot(user_id="test_user", avatar=avatar)
        response = bot.handle_message(test_message)
        print(f"\n🧑‍🎤 Avatar: {avatar}")
        print("💬 FlowBot says:", response)