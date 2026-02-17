# backend/agent.py

import os
import psutil
from datetime import datetime
from typing import Optional


class Agent:

    def __init__(self):
        self.pending_action = None  # untuk konfirmasi shutdown

        self.tools = {
            "get_time": self.get_current_time,
            "get_system_status": self.get_system_status,
            "shutdown": self.shutdown_pc
        }

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def handle(self, user_message: str) -> Optional[str]:

        # Cek konfirmasi shutdown dulu
        if self.pending_action == "shutdown_confirm":
            if user_message.lower() in ["ya", "yes", "confirm", "oke"]:
                self.pending_action = None
                return self.execute_shutdown()
            else:
                self.pending_action = None
                return "Shutdown dibatalkan."

        intent = self.detect_intent(user_message)

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

        return None

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
            f"Status Sistem:\n"
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