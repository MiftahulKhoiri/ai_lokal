import os
import json

DATA_DIR = "data"

FILES = {
    "prompt": "system_prompt.txt",
    "ai": "ai_config.json",
    "user": "user_profile.json",
}

DEFAULT_AI_CONFIG = {
    "model_name": "7B",
    "max_tokens": 256,
    "temperature": 0.4,
    "stream": True
}

DEFAULT_USER_PROFILE = {
    "name": "",
    "role": "",
    "language": "Indonesia",
    "mode": "developer"
}


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Prompt file (text)
    prompt_path = os.path.join(DATA_DIR, FILES["prompt"])
    if not os.path.exists(prompt_path):
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("")

    # AI config (json)
    ai_path = os.path.join(DATA_DIR, FILES["ai"])
    if not os.path.exists(ai_path):
        with open(ai_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_AI_CONFIG, f, indent=4)

    # User profile (json)
    user_path = os.path.join(DATA_DIR, FILES["user"])
    if not os.path.exists(user_path):
        with open(user_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USER_PROFILE, f, indent=4)


def load_text_file(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_json_file(filename: str) -> dict:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_configs():
    ensure_data_files()

    return {
        "system_prompt": load_text_file(FILES["prompt"]),
        "ai_config": load_json_file(FILES["ai"]),
        "user_profile": load_json_file(FILES["user"]),
    }