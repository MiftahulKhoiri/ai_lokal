import os
import sys
import subprocess
import signal
import time
import requests
from tools.bootstrap import bootstrap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"

MODEL_FILE = "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
LLAMA_PORT = 8081
FLASK_PORT = 5000

llama_process = None
gunicorn_process = None

bootstrap()


# ===============================
# Utility
# ===============================
def kill_port(port):
    os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")


def wait_for_llama(timeout=120):
    print(f"[INFO] Menunggu llama-server port {LLAMA_PORT} siap...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            r = requests.get(
                f"http://127.0.0.1:{LLAMA_PORT}/health",
                timeout=2
            )
            if r.status_code == 200:
                print("[INFO] llama-server siap.")
                return True
        except:
            pass
        time.sleep(1)

    raise RuntimeError("llama-server gagal start.")


# ===============================
# Start llama-server
# ===============================
def start_llama():
    global llama_process

    model_path = os.path.join(MODEL_DIR, MODEL_FILE)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    print(f"[INFO] Membersihkan port {LLAMA_PORT}...")
    kill_port(LLAMA_PORT)

    cmd = [
        LLAMA_PATH,
        "-m", model_path,
        "--host", "127.0.0.1",
        "--port", str(LLAMA_PORT),
        "--ctx-size", "2048",
        "--threads", "8",
        "--batch-size", "512",
        "--n-gpu-layers", "0"
    ]

    print("[INFO] Menjalankan model 7B...")
    llama_process = subprocess.Popen(cmd)

    wait_for_llama()


# ===============================
# Start Gunicorn
# ===============================
def start_gunicorn():
    global gunicorn_process

    print(f"[INFO] Membersihkan port {FLASK_PORT}...")
    kill_port(FLASK_PORT)

    cmd = [
        sys.executable,
        "-m", "gunicorn",
        "backend.app:app",
        "-k", "gevent",
        "-w", "1",
        "--worker-connections", "1000",
        "--timeout", "120",
        "-b", f"0.0.0.0:{FLASK_PORT}"
    ]

    print("[INFO] Menjalankan Gunicorn...")
    gunicorn_process = subprocess.Popen(cmd)


# ===============================
# Shutdown
# ===============================
def shutdown(signum, frame):
    print("\n[INFO] Shutdown server...")

    if gunicorn_process:
        gunicorn_process.terminate()

    if llama_process:
        llama_process.terminate()

    sys.exit(0)


# ===============================
# Main
# ===============================
if __name__ == "__main__":

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("[INFO] Loading memory...")
    from backend.memory import load_memory
    load_memory()

    start_llama()
    start_gunicorn()

    print("\n[INFO] AI Lokal Production Server Running")
    print("Local   : http://127.0.0.1:5000")
    print("LAN     : http://IP_RASPBERRY_PI:5000\n")

    while True:
        time.sleep(1)