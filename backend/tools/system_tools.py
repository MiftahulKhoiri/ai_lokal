import os
import subprocess
from .security import safe_path
import psutil
from datetime import datetime


def get_current_time():

    now = datetime.now()

    hari_map = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu",
    }

    hari = hari_map.get(now.strftime("%A"), now.strftime("%A"))

    return (
        f"Hari ini {hari}, "
        f"{now.strftime('%d %B %Y')}.\n"
        f"Sekarang pukul {now.strftime('%H:%M:%S')}."
    )


def get_system_status():

    cpu = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory()

    disk = psutil.disk_usage("/")

    total_ram = round(ram.total / (1024**3), 2)
    used_ram = round(ram.used / (1024**3), 2)
    free_ram = round(ram.available / (1024**3), 2)

    return (
        "Status Sistem\n\n"
        f"CPU Usage : {cpu}%\n"
        f"RAM Total : {total_ram} GB\n"
        f"RAM Used  : {used_ram} GB\n"
        f"RAM Free  : {free_ram} GB\n"
        f"Disk Usage: {disk.percent}%"
    )


def file_info(path: str) -> str:

    try:

        path = safe_path(path)

        if not os.path.exists(path):
            return "File tidak ditemukan"

        stat = os.stat(path)

        return f"""
PATH: {path}
SIZE: {stat.st_size} bytes
MODIFIED: {stat.st_mtime}
"""

    except Exception as e:
        return f"file_info error: {e}"


def run_python(path: str) -> str:

    try:

        path = safe_path(path)

        if not os.path.exists(path):
            return "File tidak ditemukan"

        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=30
        )

        return f"""
RETURN CODE: {result.returncode}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""

    except subprocess.TimeoutExpired:
        return "Eksekusi timeout"

    except Exception as e:
        return f"run_python error: {e}"


def run_shell(command: str) -> str:

    try:

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        return f"""
RETURN CODE: {result.returncode}

STDOUT:
{result.stdout}

STDERR:
{result.stderr}
"""

    except subprocess.TimeoutExpired:
        return "Command timeout"

    except Exception as e:
        return f"run_shell error: {e}"


def project_tree(path: str = ".", max_depth: int = 3) -> str:

    try:

        path = safe_path(path)

        tree = []

        for root, dirs, files in os.walk(path):

            level = root.replace(path, "").count(os.sep)

            if level > max_depth:
                continue

            indent = " " * (level * 2)

            tree.append(f"{indent}{os.path.basename(root)}/")

            subindent = " " * ((level + 1) * 2)

            for f in files:
                tree.append(f"{subindent}{f}")

        return "\n".join(tree)

    except Exception as e:
        return f"project_tree error: {e}"