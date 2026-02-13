import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "chat_history.json")

MAX_HISTORY = 20  # batasi jumlah percakapan disimpan

chat_history = []


def load_memory():
    global chat_history

    if not os.path.exists(DATA_PATH):
        chat_history = []
        return

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            chat_history = json.load(f)
    except:
        chat_history = []


def save_memory():
    try:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(chat_history[-MAX_HISTORY:], f, indent=2, ensure_ascii=False)
    except:
        pass


def add_to_memory(user, assistant):
    global chat_history

    chat_history.append({
        "role": "user",
        "content": user
    })

    chat_history.append({
        "role": "assistant",
        "content": assistant
    })

    save_memory()


def get_memory():
    return chat_history[-MAX_HISTORY:]