import os
import sys
import socket
import signal
import subprocess
import time

# ===============================
# Konfigurasi
# ===============================

FLASK_PORT = 5000

gunicorn_process = None


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
    try:
        subprocess.run(
            ["fuser", "-k", f"{port}/tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


# ===============================
# Start Gunicorn
# ===============================

def start_gunicorn():

    global gunicorn_process

    print(f"[INFO] Membersihkan port {FLASK_PORT}...")
    kill_port(FLASK_PORT)

    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "backend.app:app",
        "-k",
        "gevent",
        "-w",
        "1",
        "--worker-connections",
        "1000",
        "--timeout",
        "120",
        "-b",
        f"0.0.0.0:{FLASK_PORT}"
    ]

    print("[INFO] Menjalankan Gunicorn...")

    gunicorn_process = subprocess.Popen(
        cmd,
        preexec_fn=os.setsid
    )

    print("[INFO] Gunicorn berjalan (PID:", gunicorn_process.pid, ")")


# ===============================
# Stop Gunicorn
# ===============================

def stop_gunicorn():

    global gunicorn_process

    if gunicorn_process is None:
        return

    if gunicorn_process.poll() is not None:
        gunicorn_process = None
        return

    print("[INFO] Menghentikan Gunicorn...")

    try:

        # Graceful shutdown
        os.killpg(os.getpgid(gunicorn_process.pid), signal.SIGTERM)

        try:
            gunicorn_process.wait(timeout=10)

        except subprocess.TimeoutExpired:

            print("[WARN] Gunicorn tidak berhenti, memaksa SIGKILL")

            os.killpg(os.getpgid(gunicorn_process.pid), signal.SIGKILL)
            gunicorn_process.wait()

    except Exception as e:

        print("[ERROR] Gagal menghentikan Gunicorn:", e)

    gunicorn_process = None

    print("[INFO] Gunicorn berhenti")


# ===============================
# Shutdown server
# ===============================

def shutdown(signum=None, frame=None):

    print("\n[INFO] Shutdown server...")

    stop_gunicorn()

    print("[INFO] Server berhasil dihentikan")

    sys.exit(0)


# ===============================
# Main program
# ===============================

if __name__ == "__main__":

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    local_ip = get_local_ip()

    print("=" * 40)
    print("SERVER STARTED")
    print(f"Local  : http://127.0.0.1:{FLASK_PORT}")
    print(f"Network: http://{local_ip}:{FLASK_PORT}")
    print("=" * 40)

    start_gunicorn()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        shutdown()