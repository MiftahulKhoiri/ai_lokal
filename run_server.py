import os
import sys
import subprocess
import signal
import time
import socket

from tools.bootstrap import bootstrap
from backend.llama_manager import start_server, stop_server
from backend.servers import (
    start_gunicorn,
    get_local_ip,
    shutdown
)

from backend.memory import load_memory



# ===============================
# Main
# ===============================
if __name__ == "__main__":

    bootstrap()

    signal.signal(signal.SIGINT, safe_shutdown)
    signal.signal(signal.SIGTERM, safe_shutdown)

    local_ip = get_local_ip()

    print("[INFO] Loading memory...")
    load_memory()

    print("[INFO] Starting LLM server...")
    start_model()

    time.sleep(5)

    print("[INFO] Starting API server...")
    start_gunicorn()

    print("\n[INFO] AI Lokal Production Server Running")
    print(f"Local   : http://127.0.0.1:5000")
    print(f"Network : http://{local_ip}:5000\n")

    while True:
        time.sleep(1)