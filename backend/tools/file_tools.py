import os
from .security import safe_path


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