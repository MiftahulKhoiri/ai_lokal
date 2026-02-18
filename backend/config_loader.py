import os
import json

DATA_DIR = "data"

FILES = {
    "prompt": "system_prompt.txt",
    "ai": "ai_config.json",
    "user": "user_profile.json",
    "review": "file_review.json",
    "agent": "agent.json",
}

# =============================
# DEFAULT DATA
# =============================

DEFAULT_SYSTEM_PROMPT = """Nama kamu adalah AIRA.
AI asisten pribadi oleh user.

Aturan umum:
- Mulai dengan menjawab salam dengan benar (waalaikumsalam warahmatullahi wabarakatuh).
- User paling suka diajak diskusi agama Islam.
- Jawaban teknis, ringkas, langsung ke inti.
- Jika diminta menulis kode, tulis dalam 1 blok kode lengkap.
- Jangan potong kode.
- Jangan selipkan penjelasan di tengah kode.
- Penjelasan boleh sebelum atau sesudah blok kode.
- Jika diajak berdiskusi, jelaskan dengan benar dan tidak asal-asalan.
"""

DEFAULT_AI_CONFIG = {
    "model_name": "7B",
    "max_tokens": 256,
    "temperature": 0.4,
    "stream": True,
    "short_term_limit": 6,
    "workspace_root": "/home/pi/ai_lokal/project"
}

DEFAULT_USER_PROFILE = {
    "name": "",
    "role": "",
    "language": "Indonesia",
    "mode": "developer"
}

DEFAULT_REVIEW_CONFIG = {
    "review_template": (
        "Berikut isi file {filename}.\n"
        "Lakukan review teknis dengan struktur berikut:\n"
        "1. Fungsi utama file\n"
        "2. Identifikasi bug\n"
        "3. Saran refactor\n"
        "4. Evaluasi kualitas arsitektur\n\n"
        "Isi file:\n{content}"
    )
}

DEFAULT_AGENT_CONFIG = {
    "allowed_actions": {
        "get_time": {"confirm": False},
        "get_system_status": {"confirm": False},
        "shutdown": {"confirm": True},
        "list_files": {"confirm": False},
        "read_file": {"confirm": False},
        "analyze_file": {"confirm": False}
    }
}

# =============================
# INTERNAL UTILITIES
# =============================

def _safe_load_json(path: str, default_data: dict):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Empty JSON file")
            return json.loads(content)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data


def _ensure_json_file(path: str, default_data: dict):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)

# =============================
# TOOL PROMPT BUILDER
# =============================

def build_tool_instruction(agent_config: dict) -> str:
    tools = agent_config.get("allowed_actions", {})

    tool_lines = ""
    for tool_name, rule in tools.items():
        confirm_text = " (butuh konfirmasi)" if rule.get("confirm") else ""
        tool_lines += f"- {tool_name}{confirm_text}\n"

    return f"""

=== AVAILABLE TOOLS ===
{tool_lines}

Aturan penggunaan tool:
- Jika pertanyaan membutuhkan data sistem nyata (waktu, CPU, RAM, file),
  WAJIB menggunakan tool.
- Jangan menjawab berdasarkan asumsi.
- Jika menggunakan tool, balas HANYA dalam format JSON:
  {{
    "action": "nama_action",
    "params": {{}}
  }}
- Setelah menerima hasil tool, berikan jawaban final ke user.
"""

# =============================
# MAIN FUNCTIONS
# =============================

def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    prompt_path = os.path.join(DATA_DIR, FILES["prompt"])

    if not os.path.exists(prompt_path):
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_SYSTEM_PROMPT)
    else:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(DEFAULT_SYSTEM_PROMPT)

    json_defaults = {
        "ai": DEFAULT_AI_CONFIG,
        "user": DEFAULT_USER_PROFILE,
        "review": DEFAULT_REVIEW_CONFIG,
        "agent": DEFAULT_AGENT_CONFIG
    }

    for key, default_data in json_defaults.items():
        path = os.path.join(DATA_DIR, FILES[key])
        _ensure_json_file(path, default_data)


def load_text_file(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_all_configs():
    ensure_data_files()

    base_prompt = load_text_file(FILES["prompt"])

    agent_config = _safe_load_json(
        os.path.join(DATA_DIR, FILES["agent"]),
        DEFAULT_AGENT_CONFIG
    )

    final_prompt = base_prompt + build_tool_instruction(agent_config)

    return {
        "system_prompt": final_prompt,
        "ai_config": _safe_load_json(
            os.path.join(DATA_DIR, FILES["ai"]),
            DEFAULT_AI_CONFIG
        ),
        "user_profile": _safe_load_json(
            os.path.join(DATA_DIR, FILES["user"]),
            DEFAULT_USER_PROFILE
        ),
        "review_config": _safe_load_json(
            os.path.join(DATA_DIR, FILES["review"]),
            DEFAULT_REVIEW_CONFIG
        ),
        "agent_config": agent_config,
    }