import os
import sys
import socket
from tools.bootstrap import bootstrap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

sys.path.append(BASE_DIR)
sys.path.append(BACKEND_DIR)

bootstrap()

from backend.app import app
from backend.llama_manager import start_server, stop_server
from backend.memory import load_memory


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


if __name__ == "__main__":

    print("[INFO] Loading memory...")
    load_memory()

    print("[INFO] Starting llama servers...")

    # 🔥 START BOTH MODELS
    start_server("3b")
    start_server("7b")

    local_ip = get_local_ip()

    print("\n[INFO] AI Lokal Server Running")
    print(f"Local   : http://127.0.0.1:5000")
    print(f"Network : http://{local_ip}:5000\n")

    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

    finally:
        print("[INFO] Shutting down llama servers...")
        stop_server("3b")
        stop_server("7b")