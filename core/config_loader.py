import yaml

def load_tollgate_config(path="tollgates.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)