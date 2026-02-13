import subprocess
import os

# ====== PATH CONFIG ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "qwen2.5-3b-instruct-q4_k_m.gguf")
LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-cli"

# ====== SYSTEM PROMPT ======
SYSTEM_PROMPT = """Anda adalah asisten pribadi lokal.
Jawaban harus jelas, teknis, ringkas, dan tidak bertele-tele.
"""

# ====== SETTINGS ======
MAX_HISTORY = 5          # batasi memory agar tidak melebihi context
MAX_TOKENS = 256
CTX_SIZE = 2048
TEMPERATURE = 0.7
TIMEOUT = 120            # detik


def build_prompt(user_input, history):
    """
    Bangun prompt dengan batasan history agar context tidak overload.
    """
    prompt = SYSTEM_PROMPT.strip() + "\n\n"

    # Ambil history terakhir saja
    recent_history = history[-MAX_HISTORY:]

    for h in recent_history:
        prompt += f"User: {h['user']}\n"
        prompt += f"Assistant: {h['assistant']}\n"

    prompt += f"User: {user_input}\nAssistant:"
    return prompt


def generate_response(user_input, history):
    """
    Jalankan llama-cli dan kembalikan response model.
    """

    if not os.path.exists(MODEL_PATH):
        return "ERROR: Model tidak ditemukan."

    if not os.path.exists(LLAMA_PATH):
        return "ERROR: llama-cli tidak ditemukan."

    prompt = build_prompt(user_input, history)

    cmd = [
        LLAMA_PATH,
        "-m", MODEL_PATH,
        "-p", prompt,
        "-n", str(MAX_TOKENS),
        "--temp", str(TEMPERATURE),
        "--ctx-size", str(CTX_SIZE),
        "--no-display-prompt"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )

        if result.returncode != 0:
            return f"ERROR: llama-cli gagal.\n{result.stderr}"

        output = result.stdout.strip()

        # Parsing lebih aman
        if "Assistant:" in output:
            response = output.split("Assistant:")[-1].strip()
        else:
            response = output.strip()

        return response if response else "Tidak ada respons dari model."

    except subprocess.TimeoutExpired:
        return "ERROR: Model timeout (terlalu lama merespons)."

    except Exception as e:
        return f"ERROR: {str(e)}"