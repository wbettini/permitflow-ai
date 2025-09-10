"""
flowbot_test.py — Quick manual test for FlowBot failback logic.
Run from project root or with PYTHONPATH set so /app is importable.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.agents.flowbot.flowbot import FlowBot

if __name__ == "__main__":
    
    bot = FlowBot(user_id="test_user", tone="friendly")
    response = bot.handle_message("This is something random")
    print("FlowBot says:", response)
    
    bot = FlowBot(user_id="test_user", tone="formal")
    response = bot.handle_message("This is something random")
    print("FlowBot says:", response)

    bot = FlowBot(user_id="test_user", tone="mentor")
    response = bot.handle_message("This is something random")
    print("FlowBot says:", response)