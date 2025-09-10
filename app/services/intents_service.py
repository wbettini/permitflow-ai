# services/intents_service.py
import random
from app.core.config import GENERAL_INTENTS

def get_fallback_response(intent_key: str, tone: str = None):
    intent_data = GENERAL_INTENTS.get(intent_key)
    if not intent_data:
        return None
    
    responses = intent_data.get("responses", [])
    
    if tone:
        responses = [r for r in responses if r.get("tone") == tone] or responses
    
    if not responses:
        return None
    
    return random.choice(responses)["text"]