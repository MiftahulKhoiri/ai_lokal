import os
import sys
import subprocess
from pathlib import Path

from core.logger import get_logger
from core.update import SelfUpdater

log = get_logger("AI_BOOTSTRAP")

BASE_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = BASE_DIR / "venv"
REQ_FILE = BASE_DIR / "requirements.txt"

DATA_PATH = BASE_DIR / "data" / "qa.json"
CONTOH_PATH = BASE_DIR / "data" / "qa_contoh.json"
MODEL_PATH = BASE_DIR / "model" / "vectorizer.pkl"


# ===============================
# VIRTUAL ENV
# ===============================

def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix


def create_venv():
    log.warning("Virtualenv belum ada, membuat venv...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    log.info("Virtualenv berhasil dibuat")


def restart_in_venv():
    python_bin = VENV_DIR / "bin" / "python"
    log.warning("Restarting aplikasi di dalam virtualenv...")
    os.execv(str(python_bin), [str(python_bin)] + sys.argv)


# ===============================
# REQUIREMENTS
# ===============================

def install_requirements():
    log.info("Memastikan dependency terinstall...")

    pip_bin = VENV_DIR / "bin" / "pip"
    subprocess.check_call([
        str(pip_bin),
        "install",
        "--upgrade",
        "-r",
        str(REQ_FILE)
    ])

    log.info("Dependency siap")


# ===============================
# BOOTSTRAP UTAMA
# ===============================

def bootstrap():
    # ===============================
    # 1. Pastikan venv
    # ===============================
    if not VENV_DIR.exists():
        create_venv()
        restart_in_venv()

    if not in_virtualenv():
        restart_in_venv()

    # ===============================
    # 2. Dependency
    # ===============================
    install_requirements()

    # ===============================
    # 3. Auto update
    # ===============================
    updater = SelfUpdater(repo_dir=str(BASE_DIR))
    if updater.update_if_needed():
        log.warning("Restart setelah update...")
        restart_in_venv()

    # ===============================
    # 4. DATASET
    # ===============================
    if not DATA_PATH.exists():
        log.warning("qa.json belum ada, generate dataset awal...")

        if not CONTOH_PATH.exists():
            raise RuntimeError("qa_contoh.json tidak ditemukan")

        subprocess.check_call(
            [
                str(VENV_DIR / "bin" / "python"),
                "-m",
                "core.generate_dataset"   # ✅ pastikan file ini ADA
            ],
            cwd=str(BASE_DIR)
        )

        log.info("Dataset awal berhasil dibuat")

    # ===============================
    # 5. VALIDASI DATASET
    # ===============================
    try:
        import json
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or not data:
            raise RuntimeError("qa.json kosong atau format salah")

        total_q = sum(len(item.get("questions", [])) for item in data)
        if total_q == 0:
            raise RuntimeError("qa.json tidak memiliki pertanyaan valid")

    except Exception as e:
        raise RuntimeError(f"Dataset tidak valid: {e}")

    # ===============================
    # 6. TRAINING MODEL
    # ===============================
    if not MODEL_PATH.exists():
        log.warning("Model belum ada, training awal...")

        subprocess.check_call(
            [
                str(VENV_DIR / "bin" / "python"),
                "-m",
                "core.trainer"
            ],
            cwd=str(BASE_DIR)
        )

        log.info("Training awal selesai")
    else:
        log.info("Model sudah ada, skip training awal")