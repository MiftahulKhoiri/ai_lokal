import os
import sys
import subprocess
import signal
import time
import requests
from tools.bootstrap import bootstrap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf")

LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"
LLAMA_PORT = 8080
FLASK_PORT = 5000

llama_process = None
gunicorn_process = None


# ===============================
# Utility
# ===============================
def kill_port(port):
    os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")


def wait_for_llama(timeout=60):
    print("[INFO] Menunggu llama-server siap...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            r = requests.get(f"http://127.0.0.1:{LLAMA_PORT}/health", timeout=2)
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

    print("[INFO] Membersihkan port 8080...")
    kill_port(LLAMA_PORT)

    cmd = [
        LLAMA_PATH,
        "-m", MODEL_PATH,
        "--host", "127.0.0.1",
        "--port", str(LLAMA_PORT),
        "--ctx-size", "2048",
        "--threads", "4"
    ]

    print("[INFO] Menjalankan llama-server...")
    llama_process = subprocess.Popen(cmd)

    wait_for_llama()


# ===============================
# Start Gunicorn
# ===============================
def start_gunicorn():
    global gunicorn_process

    print("[INFO] Membersihkan port 5000...")
    kill_port(FLASK_PORT)

    cmd = [
        "gunicorn",
        "-w", "2",
        "--worker-class", "gthread",
        "--threads", "4",
        "--timeout", "120",
        "-b", f"0.0.0.0:{FLASK_PORT}",
        "backend.app:app"
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
    print("Network : http://0.0.0.0:5000\n")

    # Keep main thread alive
    while True:
        time.sleep(1)