import os

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