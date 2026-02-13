import os
import sys

# Tambahkan folder backend ke PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

sys.path.append(BACKEND_DIR)

from backe import app

if __name__ == "__main__":
    print("🚀 AI Lokal Server Starting...")
    print("📡 Akses via: http://0.0.0.0:5000")
    print("🌐 Atau: http://IP_RASPBERRY_PI:5000\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )