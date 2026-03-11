import os
import sys
import subprocess
import signal
import time
import requests
import socket
from tools.bootstrap import bootstrap
from backend.servers import start_gunicorn. get_local_ip. kill_port.shutdown
from backend.memory import load_memory


# ===============================
# Main
# ===============================
if __name__ == "__main__":

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    local_ip = get_local_ip()

    print("[INFO] Loading memory...")
    load_memory()
    

    start_llama()
    start_gunicorn()

    print("\n[INFO] AI Lokal Production Server Running")
    print(f"Network : http://{local_ip}:5000\n")

    while True:
        time.sleep(1)