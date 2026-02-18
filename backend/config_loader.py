import os
import json

DATA_DIR = "data"

FILES = {
    "prompt": "system_prompt.txt",
    "ai": "ai_config.json",
    "user": "user_profile.json",
    "review": "file_review.json",
    "agent": "agent.json",
}

DEFAULT_AI_CONFIG = {
    "model_name": "7B",
    "max_tokens": 256,
    "temperature": 0.4,
    "stream": True,
    "short_term_limit": 6,
    "workspace_root": "/home/pi/ai_lokal/project"
}

DEFAULT_USER_PROFILE = {
    "name": "",
    "role": "",
    "language": "Indonesia",
    "mode": "developer"
}

DEFAULT_REVIEW_CONFIG = {
    "review_template": (
        "Berikut isi file {filename}.\n"
        "Lakukan review teknis dengan struktur berikut:\n"
        "1. Fungsi utama file\n"
        "2. Identifikasi bug\n"
        "3. Saran refactor\n"
        "4. Evaluasi kualitas arsitektur\n\n"
        "Isi file:\n{content}"
    )
}

DEFAULT_AGENT_CONFIG = {
    "allowed_actions": {
        "get_time": {"confirm": False},
        "get_system_status": {"confirm": False},
        "shutdown": {"confirm": True},
        "list_files": {"confirm": False},
        "read_file": {"confirm": False},
        "analyze_file": {"confirm": False}
    }
}


# =============================
# INTERNAL UTILITIES
# =============================

def _safe_load_json(path: str, default_data: dict):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Empty JSON file")
            return json.loads(content)
    except Exception:
        # Reset jika kosong / corrupt
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data


def _ensure_json_file(path: str, default_data: dict):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)


# =============================
# MAIN FUNCTIONS
# =============================

def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Prompt (text)
    prompt_path = os.path.join(DATA_DIR, FILES["prompt"])
    if not os.path.exists(prompt_path):
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write("")

    # JSON files
    for key in ["ai", "user", "review", "agent"]:
        path = os.path.join(DATA_DIR, FILES[key])

        if key == "ai":
            _ensure_json_file(path, DEFAULT_AI_CONFIG)
        elif key == "user":
            _ensure_json_file(path, DEFAULT_USER_PROFILE)
        elif key == "review":
            _ensure_json_file(path, DEFAULT_REVIEW_CONFIG)
        elif key == "agent":
            _ensure_json_file(path, DEFAULT_AGENT_CONFIG)


def load_text_file(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_all_configs():
    ensure_data_files()

    return {
        "system_prompt": load_text_file(FILES["prompt"]),
        "ai_config": _safe_load_json(
            os.path.join(DATA_DIR, FILES["ai"]),
            DEFAULT_AI_CONFIG
        ),
        "user_profile": _safe_load_json(
            os.path.join(DATA_DIR, FILES["user"]),
            DEFAULT_USER_PROFILE
        ),
        "review_config": _safe_load_json(
            os.path.join(DATA_DIR, FILES["review"]),
            DEFAULT_REVIEW_CONFIG
        ),
        "agent_config": _safe_load_json(
            os.path.join(DATA_DIR, FILES["agent"]),
            DEFAULT_AGENT_CONFIG
        ),
    }