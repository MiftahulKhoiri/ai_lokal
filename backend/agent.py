import os
import json
import psutil
from datetime import datetime
from typing import Optional


class Agent:

    def __init__(self, agent_config: dict, workspace_root: str):
        self.pending_action = None
        self.agent_config = agent_config or {}
        self.allowed_actions = self.agent_config.get("allowed_actions", {})
        self.workspace_root = os.path.abspath(workspace_root)

        self.tools = {
            "get_time": self.get_current_time,
            "get_system_status": self.get_system_status,
            "shutdown": self.execute_shutdown,
            "list_files": self.list_files,
            "read_file": self.read_file,
        }

    # =========================
    # HYBRID ENTRY POINT
    # =========================

    def execute_action(self, action_json: str):
        """
        Expected JSON format:
        {
            "action": "get_time",
            "params": {}
        }
        """

        # Pending confirmation
        if self.pending_action:
            if action_json.lower() in ["ya", "yes", "confirm", "oke"]:
                action = self.pending_action
                self.pending_action = None
                return self.tools[action]()
            else:
                self.pending_action = None
                return "Aksi dibatalkan."

        # Parse JSON
        try:
            data = json.loads(action_json)
        except Exception:
            return None  # bukan JSON → lanjut ke chat biasa

        action = data.get("action")
        params = data.get("params", {})

        if action not in self.allowed_actions:
            return None

        rule = self.allowed_actions[action]

        if action not in self.tools:
            return None

        # Jika perlu konfirmasi
        if rule.get("confirm", False):
            self.pending_action = action
            return f"Konfirmasi untuk menjalankan '{action}'. Ketik 'ya' untuk lanjut."

        try:
            if params:
                return self.tools[action](**params)
            return self.tools[action]()
        except Exception as e:
            return f"Gagal menjalankan action: {e}"

    # =========================
    # SECURITY
    # =========================

    def safe_path(self, relative_path: str) -> str:
        full_path = os.path.abspath(
            os.path.join(self.workspace_root, relative_path)
        )

        if not full_path.startswith(self.workspace_root):
            raise PermissionError("Akses ditolak: di luar workspace.")

        return full_path

    # =========================
    # SYSTEM TOOLS
    # =========================

    def get_current_time(self) -> str:
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

        hari_id = hari_map.get(now.strftime("%A"), now.strftime("%A"))

        return (
            f"Hari ini {hari_id}, "
            f"tanggal {now.strftime('%d-%m-%Y')}, "
            f"jam {now.strftime('%H:%M:%S')}"
        )

    def get_system_status(self) -> str:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()

        return (
            "Status Sistem:\n"
            f"- CPU Usage: {cpu}%\n"
            f"- RAM Usage: {ram.percent}%\n"
            f"- RAM Tersedia: {round(ram.available / (1024**3), 2)} GB"
        )

    def execute_shutdown(self) -> str:
        try:
            if os.name == "nt":
                os.system("shutdown /s /t 5")
            else:
                os.system("shutdown -h now")

            return "Perintah shutdown dijalankan."
        except Exception as e:
            return f"Gagal menjalankan shutdown: {e}"

    # =========================
    # WORKSPACE TOOLS
    # =========================

    def list_files(self) -> str:
        try:
            items = os.listdir(self.workspace_root)
            if not items:
                return "Workspace kosong."
            return "Isi workspace:\n" + "\n".join(items)
        except Exception as e:
            return f"Gagal membaca workspace: {e}"

    def read_file(self, filename: str) -> str:
        try:
            path = self.safe_path(filename)

            if not os.path.isfile(path):
                return "File tidak ditemukan."

            with open(path, "r", encoding="utf-8") as f:
                return f.read(8000)

        except Exception as e:
            return f"Gagal membaca file: {e}"