import yaml
from pathlib import Path


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "triage.yaml"


def load_prompt():

    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        prompt = yaml.safe_load(file)

    return prompt