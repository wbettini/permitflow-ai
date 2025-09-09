import yaml
from app.core.config import TOLLGATE_PROMPTS_FILE

def load_tollgate_config(path=TOLLGATE_PROMPTS_FILE):

    with open(path, "r") as f:
        return yaml.safe_load(f)