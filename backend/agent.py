import os
import json
import psutil
from datetime import datetime


class Agent:

    def __init__(self, agent_config: dict, workspace_root: str):

        self.agent_config = agent_config or {}
        self.allowed_actions = self.agent_config.get("allowed_actions", {})
        self.workspace_root = os.path.abspath(workspace_root)

        self.tools = {
            "get_current_time": self.get_current_time,
            "get_system_status": self.get_system_status,
            "list_files": self.list_files,
            "read_file": self.read_file,
        }

    # =========================
    # TOOL EXECUTION
    # =========================

    def run(self, tool_name: str, params: dict | None = None):

        if tool_name not in self.tools:
            return f"Tool '{tool_name}' tidak tersedia."

        try:

            tool = self.tools[tool_name]

            if params:
                return tool(**params)

            return tool()

        except Exception as e:
            return f"Gagal menjalankan tool: {e}"

    # =========================
    # SECURITY
    # =========================

    def safe_path(self, relative_path: str):

        full_path = os.path.abspath(
            os.path.join(self.workspace_root, relative_path)
        )

        if not full_path.startswith(self.workspace_root):
            raise PermissionError("Akses di luar workspace ditolak.")

        return full_path

    # =========================
    # SYSTEM TOOLS
    # =========================

    def get_current_time(self):

        now = datetime.now()

        hari_map = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu",
        }

        hari = hari_map.get(now.strftime("%A"), now.strftime("%A"))

        return (
            f"Selamat {hari}. "
            f"Hari ini tanggal {now.strftime('%d-%m-%Y')}. "
            f"Sekarang pukul {now.strftime('%H:%M:%S')}."
        )

    def get_system_status(self):

        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()

        return (
            "Status Sistem:\n"
            f"CPU Usage: {cpu}%\n"
            f"RAM Usage: {ram.percent}%"
        )

    # =========================
    # FILE TOOLS
    # =========================

    def list_files(self):

        items = os.listdir(self.workspace_root)

        if not items:
            return "Workspace kosong."

        return "\n".join(items)

    def read_file(self, filename: str):

        path = self.safe_path(filename)

        if not os.path.isfile(path):
            return "File tidak ditemukan."

        with open(path, "r", encoding="utf-8") as f:
            return f.read(8000)