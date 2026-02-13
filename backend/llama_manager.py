import subprocess
import requests
import time
import os
import signal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf")
LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"

LLAMA_URL = "http://127.0.0.1:8080/health"
LLAMA_PORT = "8080"

process = None


def is_running():
    try:
        r = requests.get(LLAMA_URL, timeout=2)
        return r.status_code == 200
    except:
        return False


def start_server():
    global process

    if is_running():
        print(" llama-server sudah berjalan.")
        return

    print(" Menjalankan llama-server...")

    cmd = [
        LLAMA_PATH,
        "-m", MODEL_PATH,
        "--host", "127.0.0.1",
        "--port", LLAMA_PORT,
        "--ctx-size", "2048",
        "--threads", "4"
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    wait_until_ready()


def wait_until_ready(timeout=60):
    print(" Menunggu model load...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_running():
            print("llama-server siap digunakan.")
            return
        time.sleep(1)

    raise RuntimeError(" llama-server gagal start.")


def stop_server():
    global process

    if process:
        print(" Menghentikan llama-server...")
        process.send_signal(signal.SIGINT)
        process.wait()