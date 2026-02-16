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

MODELS = {
    "3b": {
        "file": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "port": 8080
    },
    "7b": {
        "file": "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
        "port": 8081
    }
}

FLASK_PORT = 5000

llama_processes = {}
gunicorn_process = None

bootstrap()


# ===============================
# Utility
# ===============================
def kill_port(port):
    os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")


def wait_for_llama(port, timeout=120):
    print(f"[INFO] Menunggu llama-server port {port} siap...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            r = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
            if r.status_code == 200:
                print(f"[INFO] llama-server {port} siap.")
                return True
        except:
            pass
        time.sleep(1)

    raise RuntimeError(f"llama-server port {port} gagal start.")


# ===============================
# Start llama-server per model
# ===============================
def start_llama(model_key):
    model_info = MODELS[model_key]
    port = model_info["port"]
    model_path = os.path.join(MODEL_DIR, model_info["file"])

    print(f"[INFO] Membersihkan port {port}...")
    kill_port(port)

    cmd = [
        LLAMA_PATH,
        "-m", model_path,
        "--host", "127.0.0.1",
        "--port", str(port),
        "--ctx-size", "2048",
        "--threads", "8",
        "--batch-size", "512",
        "--n-gpu-layers", "0"
    ]

    print(f"[INFO] Menjalankan model {model_key} di port {port}...")
    process = subprocess.Popen(cmd)

    llama_processes[model_key] = process
    wait_for_llama(port)


# ===============================
# Start Gunicorn (Streaming Friendly)
# ===============================
def start_gunicorn():
    global gunicorn_process

    print("[INFO] Membersihkan port 5000...")
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

    for process in llama_processes.values():
        process.terminate()

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

    # Start both models
    start_llama("3b")
    start_llama("7b")

    # Start Flask via Gunicorn
    start_gunicorn()

    print("\n[INFO] AI Lokal Production Server Running")
    print("Local   : http://127.0.0.1:5000")
    print("LAN     : http://IP_RASPBERRY_PI:5000\n")

    while True:
        time.sleep(1)