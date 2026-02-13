import os
import sys
import socket
import signal
from tools.bootstrap import bootstrap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

sys.path.append(BASE_DIR)
sys.path.append(BACKEND_DIR)

bootstrap()

from backend.app import app
from backend.llama_manager import start_server, stop_server


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

    # 🔥 Start llama-server otomatis
    start_server()

    local_ip = get_local_ip()

    print("\n🚀 AI Lokal Server Starting...")
    print(f"📡 Local  : http://127.0.0.1:5000")
    print(f"🌐 Network: http://{local_ip}:5000\n")

    try:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    finally:
        stop_server()