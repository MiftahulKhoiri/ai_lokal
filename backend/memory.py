import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "chat_history.json")

MAX_HISTORY = 20  # jumlah message pair (user+assistant)

# Struktur baru:
# [
#   {"role": "user", "content": "..."},
#   {"role": "assistant", "content": "..."}
# ]

chat_history = []


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_memory():
    global chat_history

    ensure_data_dir()

    if not os.path.exists(DATA_PATH):
        chat_history = []
        return

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                chat_history = data[-(MAX_HISTORY * 2):]
            else:
                chat_history = []

    except Exception:
        chat_history = []


def save_memory():
    ensure_data_dir()

    try:
        trimmed = chat_history[-(MAX_HISTORY * 2):]

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)

    except Exception:
        pass


def add_to_memory(user_message, assistant_message):
    global chat_history

    chat_history.append({
        "role": "user",
        "content": user_message
    })

    chat_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    save_memory()


def get_memory():
    return chat_history[-(MAX_HISTORY * 2):]