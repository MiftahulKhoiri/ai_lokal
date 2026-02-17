# backend/agent.py

from datetime import datetime
from typing import Optional, Dict


class Agent:

    def __init__(self):
        self.tools = {
            "get_time": self.get_current_time,
        }

    # =========================
    # PUBLIC ENTRY POINT
    # =========================
    def handle(self, user_message: str) -> Optional[str]:
        """
        Cek apakah ada system intent.
        Jika ada → jalankan tool.
        Jika tidak → return None (biar lanjut ke LLM).
        """
        intent = self.detect_intent(user_message)

        if intent and intent in self.tools:
            return self.tools[intent]()

        return None

    # =========================
    # INTENT DETECTION
    # =========================
    def detect_intent(self, text: str) -> Optional[str]:
        text = text.lower()

        if "jam berapa" in text or "waktu sekarang" in text:
            return "get_time"

        if "hari apa" in text or "tanggal berapa" in text:
            return "get_time"

        return None

    # =========================
    # TOOLS
    # =========================
    def get_current_time(self) -> str:
        now = datetime.now()
        return (
            f"Hari ini {now.strftime('%A')}, "
            f"tanggal {now.strftime('%Y-%m-%d')}, "
            f"jam {now.strftime('%H:%M:%S')}"
        )