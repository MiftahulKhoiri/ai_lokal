import subprocess
import requests
import time
import os
import signal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"

# =============================
# SINGLE MODEL CONFIG (7B ONLY)
# =============================

MODEL_FILE = "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
PORT = "8081"

process = None


# =============================
# UTILITIES
# =============================

def get_health_url():
    return f"http://127.0.0.1:{PORT}/health"


def is_running():
    try:
        r = requests.get(get_health_url(), timeout=2)
        return r.status_code == 200
    except requests.RequestException:
        return False


# =============================
# SERVER CONTROL
# =============================

def start_server():
    global process

    model_path = os.path.join(MODEL_DIR, MODEL_FILE)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    if is_running():
        print(f"Model sudah berjalan di port {PORT}.")
        return

    print(f"Menjalankan 7B di port {PORT}...")

    cmd = [
        LLAMA_PATH,
        "-m", model_path,
        "--host", "127.0.0.1",
        "--port", PORT,
        "--ctx-size", "2048",
        "--threads", "8",
        "--batch-size", "512",
        "--n-gpu-layers", "0"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    wait_until_ready()


def wait_until_ready(timeout=120):
    print("Menunggu model load...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_running():
            print("Model siap digunakan.")
            return
        time.sleep(1)

    raise RuntimeError("Model gagal start.")


def stop_server():
    global process

    if process is None:
        print("Model tidak sedang berjalan.")
        return

    print("Menghentikan model 7B...")
    process.send_signal(signal.SIGINT)
    process.wait()
    process = None
    print("Model berhenti.")


# =============================
# ENTRY POINT (OPTIONAL)
# =============================

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        stop_server()