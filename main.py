import os
import sys
import socket
from tools.bootstrap import bootstrap

# ====== SETUP PATH ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.append(BASE_DIR)
sys.path.append(BACKEND_DIR)

bootstrap()

# Import setelah bootstrap & path setup
from backend.app import app


# ====== FUNCTION CEK IP ======
def get_local_ip():
    """
    Mendapatkan IP lokal Raspberry Pi.
    Tidak menggunakan hostname (kadang return 127.0.0.1).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Tidak benar-benar kirim data
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = get_local_ip()

    print(" AI Lokal Server Starting...")
    print(f" Local Access  : http://127.0.0.1:5000")
    print(f" Network Access: http://{local_ip}:5000\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )