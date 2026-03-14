import os
import subprocess
from typing import List

# ==============================
# SAFETY ROOT
# ==============================

WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", ".")


def safe_path(path: str) -> str:
    """
    Membatasi akses hanya di dalam workspace
    """

    abs_root = os.path.abspath(WORKSPACE_ROOT)
    abs_path = os.path.abspath(os.path.join(abs_root, path))

    if not abs_path.startswith(abs_root):
        raise PermissionError("Akses di luar workspace tidak diizinkan")

    return abs_path


# ==============================
# FILE OPERATIONS
# ==============================

def read_file(path: str) -> str:

    try:

        path = safe_path(path)

        if not os.path.exists(path):
            return f"File tidak ditemukan: {path}"

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except Exception as e:
        return f"read_file error: {e}"


def write_file(path: str, content: str) -> str:

    try:

        path = safe_path(path)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"File berhasil ditulis: {path}"

    except Exception as e:
        return f"write_file error: {e}"


def append_file(path: str, content: str) -> str:

    try:

        path = safe_path(path)

        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

        return "Append berhasil"

    except Exception as e:
        return f"append_file error: {e}"


def delete_file(path: str) -> str:

    try:

        path = safe_path(path)

        if not os.path.exists(path):
            return "File tidak ditemukan"

        os.remove(path)

        return "File berhasil dihapus"

    except Exception as e:
        return f"delete_file error: {e}"


# ==============================
# DIRECTORY OPERATIONS
# ==============================

def list_files(path: str = ".") -> str:

    try:

        path = safe_path(path)

        files = os.listdir(path)

        if not files:
            return "Folder kosong"

        return "\n".join(files)

    except Exception as e:
        return f"list_files error: {e}"


def make_directory(path: str) -> str:

    try:

        path = safe_path(path)

        os.makedirs(path, exist_ok=True)

        return "Directory dibuat"

    except Exception as e:
        return f"make_directory error: {e}"


# ==============================
# SEARCH
# ==============================

def search_text(path: str, query: str) -> str:

    try:

        path = safe_path(path)

        matches: List[str] = []

        for root, _, files in os.walk(path):

            for file in files:

                full_path = os.path.join(root, file)

                try:

                    with open(full_path, "r", encoding="utf-8") as f:

                        for i, line in enumerate(f, 1):

                            if query in line:
                                matches.append(
                                    f"{full_path}:{i}:{line.strip()}"
                                )

                except:
                    continue

        if not matches:
            return "Tidak ditemukan"

        return "\n".join(matches[:100])

    except Exception as e:
        return f"search_text error: {e}"


# ==============================
# FILE INFO
# ==============================

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


# ==============================
# RUN PYTHON
# ==============================

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


# ==============================
# TERMINAL COMMAND
# ==============================

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


# ==============================
# PROJECT TREE
# ==============================

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

