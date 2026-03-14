import subprocess
import requests
import time
import os
import signal

# =============================
# PATH CONFIG
# =============================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-server"

# =============================
# MODEL CONFIG
# =============================

MODEL_FILE = "qwen2.5-3b-instruct-q4_k_m.gguf"
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
# START SERVER
# =============================

def start_server():
    global process

    model_path = os.path.join(MODEL_DIR, MODEL_FILE)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    # Jika server sudah running
    if is_running():
        print(f"[INFO] Model sudah berjalan di port {PORT}")
        return

    print(f"[INFO] Menjalankan model di port {PORT}...")

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

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
    except Exception as e:
        raise RuntimeError(f"Gagal menjalankan llama-server: {e}")

    wait_until_ready()


# =============================
# WAIT UNTIL MODEL READY
# =============================

def wait_until_ready(timeout=120):

    print("[INFO] Menunggu model load...")

    start_time = time.time()

    while time.time() - start_time < timeout:

        if is_running():
            print("[INFO] Model siap digunakan")
            return

        time.sleep(1)

    raise RuntimeError("Model gagal start dalam waktu yang ditentukan")


# =============================
# STOP SERVER (SAFE SHUTDOWN)
# =============================

def stop_server():
    global process

    if process is None:
        print("[INFO] Model tidak sedang berjalan")
        return

    # Jika proses sudah mati
    if process.poll() is not None:
        process = None
        print("[INFO] Model sudah berhenti")
        return

    print("[INFO] Menghentikan model...")

    try:

        # Graceful shutdown
        os.killpg(os.getpgid(process.pid), signal.SIGINT)

        try:
            process.wait(timeout=10)

        except subprocess.TimeoutExpired:

            print("[WARN] SIGINT gagal, mencoba SIGTERM")

            os.killpg(os.getpgid(process.pid), signal.SIGTERM)

            try:
                process.wait(timeout=5)

            except subprocess.TimeoutExpired:

                print("[WARN] SIGTERM gagal, memaksa SIGKILL")

                os.killpg(os.getpgid(process.pid), signal.SIGKILL)

                process.wait()

    except Exception as e:
        print("[ERROR] Gagal menghentikan model:", e)

    process = None

    print("[INFO] Model berhasil dihentikan")


# =============================
# ENTRY POINT (OPTIONAL)
# =============================

if __name__ == "__main__":

    try:

        start_server()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        stop_server()