import os
import subprocess

# ===============================
# Path konfigurasi
# ===============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"
MODEL_FILE = "qwen2.5-3b-instruct-q4_k_m.gguf"

LLAMA_PORT = 8080

llama_process = None


# ===============================
# Ambil full path model
# ===============================
def get_model_path():
    model_path = os.path.join(MODEL_DIR, MODEL_FILE)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    return model_path


# ===============================
# Jalankan model
# ===============================
def start_model():
    global llama_process

    model_path = get_model_path()

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


    print("[INFO] Menjalankan model...")
    print(f"[INFO] Model: {MODEL_FILE}")

    llama_process = subprocess.Popen(cmd)

    return llama_process


# ===============================
# Stop model
# ===============================
def stop_model():

    global llama_process

    if llama_process:
        print("[INFO] Menghentikan model...")
        llama_process.terminate()
        llama_process.wait()


# ===============================
# Cek status model
# ===============================
def model_running():

    if llama_process is None:
        return False

    return llama_process.poll() is None