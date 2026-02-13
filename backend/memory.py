chat_history = []

def add_to_memory(user, assistant):
    chat_history.append({
        "user": user,
        "assistant": assistant
    })

def get_memory():
    return chat_history