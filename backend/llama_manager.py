import subprocess
import requests
import time
import os
import signal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"

MODELS = {
    "3b": {
        "file": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "port": "8080"
    },
    "7b": {
        "file": "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
        "port": "8081"
    }
}

processes = {}


def get_health_url(port):
    return f"http://127.0.0.1:{port}/health"


def is_running(port):
    try:
        r = requests.get(get_health_url(port), timeout=2)
        return r.status_code == 200
    except:
        return False


def start_server(model_key):
    if model_key not in MODELS:
        print("Model tidak valid.")
        return

    model_info = MODELS[model_key]
    model_path = os.path.join(MODEL_DIR, model_info["file"])
    port = model_info["port"]

    if is_running(port):
        print(f"Model {model_key} sudah berjalan di port {port}.")
        return

    print(f"Menjalankan model {model_key} di port {port}...")

    cmd = [
        LLAMA_PATH,
        "-m", model_path,
        "--host", "127.0.0.1",
        "--port", port,
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

    processes[model_key] = process
    wait_until_ready(port)


def wait_until_ready(port, timeout=120):
    print("Menunggu model load...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        if is_running(port):
            print("Model siap digunakan.")
            return
        time.sleep(1)

    raise RuntimeError("Model gagal start.")


def stop_server(model_key):
    if model_key in processes:
        print(f"Menghentikan model {model_key}...")
        processes[model_key].send_signal(signal.SIGINT)
        processes[model_key].wait()
        del processes[model_key]


def stop_all():
    for model_key in list(processes.keys()):
        stop_server(model_key)