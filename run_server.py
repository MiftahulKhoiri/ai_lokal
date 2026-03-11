import os
import sys
import subprocess
import signal
import time
import socket

from tools.bootstrap import bootstrap
from backend.model_runner import start_model, stop_model
from backend.servers import (
    start_gunicorn
    get_local_ip,
    kill_port,
    shutdown
)

from backend.memory import load_memory


# ===============================
# Main
# ===============================
if __name__ == "__main__":

    # Bootstrap system
    bootstrap()

    # Signal handler
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

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

    # Keep alive
    while True:
        time.sleep(1)