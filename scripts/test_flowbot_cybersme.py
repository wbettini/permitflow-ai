from agents.flowbot.flowbot import FlowBot
from core.state_manager import StateManager  # <-- correct import path

# Define the required fields for this test
required_fields = ["service_name", "owner", "data_classification"]

# Create state manager and FlowBot
state = StateManager()
bot = FlowBot(state, required_fields)

# Start the application
print(bot.start("cloud service permit"))

# Step 1: Provide partial info
print(bot.next_step({"service_name": "MyCloudX"}))

# Step 2: Provide remaining info to trigger CyberSME
print(bot.next_step({
    "owner": "Bill",
    "data_classification": "Confidential"
}))