import os
import subprocess
from .security import safe_path


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