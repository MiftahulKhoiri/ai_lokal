import json
from backend.dev_tools import *


def execute_tool(tool_json: str):
    """
    Menjalankan tool dari JSON action
    """

    try:
        data = json.loads(tool_json)

        action = data.get("action")

        if action == "get_system_status":
            return get_system_status()

        if action == "get_memory":
            return get_memory()

        if action == "get_cpu":
            return get_cpu()

        return "Tool tidak dikenal"

    except Exception as e:
        return f"Tool error: {str(e)}"