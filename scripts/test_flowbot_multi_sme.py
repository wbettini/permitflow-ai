# test_flowbot_multi_sme.py
from app.agents.flowbot.flowbot import FlowBot
from core.state_manager import StateManager

required_fields = ["service_name", "owner", "data_classification"]

state = StateManager()
bot = FlowBot(state, required_fields)

print(bot.start("cloud service permit"))
print(bot.next_step({"service_name": "MyCloudX"}))
print(bot.next_step({
    "owner": "Bill",
    "data_classification": "Confidential"
}))