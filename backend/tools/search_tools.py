import os
from typing import List
from .security import safe_path


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