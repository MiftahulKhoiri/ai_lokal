import os
import json

DATA_DIR = "data"

FILES = {
    "prompt": "system_prompt.txt",
    "ai": "ai_config.json",
    "user": "user_profile.json",
    "review": "file_review.json",
}

DEFAULT_AI_CONFIG = {
    "model_name": "7B",
    "max_tokens": 256,
    "temperature": 0.4,
    "stream": True,
    "short_term_limit": 6
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


# =============================
# INTERNAL UTILITIES
# =============================

def _safe_load_json(path: str, default_data: dict):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Jika corrupt → reset ke default
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

    # AI config
    ai_path = os.path.join(DATA_DIR, FILES["ai"])
    _ensure_json_file(ai_path, DEFAULT_AI_CONFIG)

    # User profile
    user_path = os.path.join(DATA_DIR, FILES["user"])
    _ensure_json_file(user_path, DEFAULT_USER_PROFILE)

    # Review config
    review_path = os.path.join(DATA_DIR, FILES["review"])
    _ensure_json_file(review_path, DEFAULT_REVIEW_CONFIG)


def load_text_file(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_all_configs():
    ensure_data_files()

    ai_path = os.path.join(DATA_DIR, FILES["ai"])
    user_path = os.path.join(DATA_DIR, FILES["user"])
    review_path = os.path.join(DATA_DIR, FILES["review"])

    return {
        "system_prompt": load_text_file(FILES["prompt"]),
        "ai_config": _safe_load_json(ai_path, DEFAULT_AI_CONFIG),
        "user_profile": _safe_load_json(user_path, DEFAULT_USER_PROFILE),
        "review_config": _safe_load_json(review_path, DEFAULT_REVIEW_CONFIG),
    }