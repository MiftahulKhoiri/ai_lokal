# backend/agent.py

import os
import psutil
from datetime import datetime
from typing import Optional

# =========================
# WORKSPACE CONFIG
# =========================

WORKSPACE_ROOT = "/home/pi/ai_lokal/project"


class Agent:

    def __init__(self):
        self.pending_action = None  # konfirmasi shutdown

        self.tools = {
            "get_time": self.get_current_time,
            "get_system_status": self.get_system_status,
            "shutdown": self.shutdown_pc,
            "list_files": self.list_files,
        }

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def handle(self, user_message: str) -> Optional[str]:

        # Konfirmasi shutdown
        if self.pending_action == "shutdown_confirm":
            if user_message.lower() in ["ya", "yes", "confirm", "oke"]:
                self.pending_action = None
                return self.execute_shutdown()
            else:
                self.pending_action = None
                return "Shutdown dibatalkan."

        intent = self.detect_intent(user_message)

        # Tool dengan parameter (baca file)
        if intent == "read_file":
            parts = user_message.split()
            if len(parts) >= 3:
                filename = parts[-1]
                return self.read_file(filename)
            return "Format: baca file namafile.py"

        if intent and intent in self.tools:
            return self.tools[intent]()

        return None

    # =========================
    # INTENT DETECTION
    # =========================
    def detect_intent(self, text: str) -> Optional[str]:
        text = text.lower()

        # Waktu
        if "jam berapa" in text or "waktu sekarang" in text:
            return "get_time"

        if "hari apa" in text or "tanggal berapa" in text:
            return "get_time"

        # System status
        if "cpu" in text or "ram" in text or "status sistem" in text:
            return "get_system_status"

        # Shutdown
        if "shutdown" in text or "matikan komputer" in text:
            return "shutdown"

        # Workspace
        if "lihat project" in text or "list project" in text:
            return "list_files"

        if "baca file" in text:
            return "read_file"

        return None

    # =========================
    # SECURITY
    # =========================
    def safe_path(self, relative_path: str) -> str:
        """
        Pastikan file tetap di dalam WORKSPACE_ROOT
        """
        full_path = os.path.abspath(
            os.path.join(WORKSPACE_ROOT, relative_path)
        )

        if not full_path.startswith(os.path.abspath(WORKSPACE_ROOT)):
            raise PermissionError("Akses ditolak: di luar workspace.")

        return full_path

    # =========================
    # TOOLS
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

    def shutdown_pc(self) -> str:
        self.pending_action = "shutdown_confirm"
        return "Apakah Anda yakin ingin mematikan komputer? Ketik 'ya' untuk konfirmasi."

    def execute_shutdown(self) -> str:
        try:
            if os.name == "nt":
                os.system("shutdown /s /t 5")
            else:
                os.system("shutdown -h now")

            return "Perintah shutdown dijalankan. Komputer akan mati."
        except Exception as e:
            return f"Gagal menjalankan shutdown: {e}"

    # =========================
    # WORKSPACE TOOLS
    # =========================

    def list_files(self) -> str:
        try:
            items = os.listdir(WORKSPACE_ROOT)
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
                content = f.read(8000)  # batas 8KB agar tidak overload LLM

            return f"Isi file {filename}:\n\n{content}"

        except Exception as e:
            return f"Gagal membaca file: {e}"