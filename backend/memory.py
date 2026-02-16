import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "chat_history.json")

MAX_HISTORY = 20  # limit per model

# Struktur:
# {
#   "3b": [ ... ],
#   "7b": [ ... ]
# }

chat_history = {
    "3b": [],
    "7b": []
}


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_memory():
    global chat_history

    ensure_data_dir()

    if not os.path.exists(DATA_PATH):
        chat_history = {"3b": [], "7b": []}
        return

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

            # Pastikan struktur valid
            if isinstance(data, dict):
                chat_history["3b"] = data.get("3b", [])
                chat_history["7b"] = data.get("7b", [])
            else:
                chat_history = {"3b": [], "7b": []}

    except:
        chat_history = {"3b": [], "7b": []}


def save_memory():
    ensure_data_dir()

    try:
        trimmed = {
            "3b": chat_history["3b"][-MAX_HISTORY:],
            "7b": chat_history["7b"][-MAX_HISTORY:]
        }

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)

    except:
        pass


def add_to_memory(user, assistant, model):
    global chat_history

    if model not in chat_history:
        chat_history[model] = []

    chat_history[model].append({
        "role": "user",
        "content": user
    })

    chat_history[model].append({
        "role": "assistant",
        "content": assistant
    })

    save_memory()


def get_memory(model):
    return chat_history.get(model, [])[-MAX_HISTORY:]