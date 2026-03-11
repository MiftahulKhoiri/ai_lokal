import os
import sys
import socket
import signal
import subprocess

# ===============================
# Konfigurasi
# ===============================
FLASK_PORT = 5000

gunicorn_process = None
llama_process = None


# ===============================
# Ambil IP lokal
# ===============================
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ===============================
# Kill port jika masih digunakan
# ===============================
def kill_port(port):
    os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")


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
# Shutdown server
# ===============================
def shutdown(signum, frame):
    global gunicorn_process
    global llama_process

    print("\n[INFO] Shutdown server...")

    if gunicorn_process:
        gunicorn_process.terminate()
        gunicorn_process.wait()

    if llama_process:
        llama_process.terminate()
        llama_process.wait()

    sys.exit(0)


# ===============================
# Main program
# ===============================
if __name__ == "__main__":

    # pasang signal handler
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    local_ip = get_local_ip()

    print("=" * 40)
    print("SERVER STARTED")
    print(f"Local  : http://127.0.0.1:{FLASK_PORT}")
    print(f"Network: http://{local_ip}:{FLASK_PORT}")
    print("=" * 40)

    start_gunicorn()

    # tunggu proses
    gunicorn_process.wait()