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
MAX_HISTORY = 5
MAX_TOKENS = 256
CTX_SIZE = 2048
TEMPERATURE = 0.7


def build_prompt(user_input, history):
    prompt = SYSTEM_PROMPT.strip() + "\n\n"

    recent_history = history[-MAX_HISTORY:]

    for h in recent_history:
        prompt += f"User: {h['user']}\n"
        prompt += f"Assistant: {h['assistant']}\n"

    prompt += f"User: {user_input}\nAssistant:"
    return prompt


def stream_response(user_input, history):
    """
    Streaming response generator.
    Menghasilkan token realtime.
    """

    if not os.path.exists(MODEL_PATH):
        yield "ERROR: Model tidak ditemukan."
        return

    if not os.path.exists(LLAMA_PATH):
        yield "ERROR: llama-cli tidak ditemukan."
        return

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

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    try:
        for line in process.stdout:
            if line.strip():
                yield line

        process.wait()

        if process.returncode != 0:
            yield "\nERROR: llama-cli gagal dijalankan."

    except Exception as e:
        yield f"\nERROR: {str(e)}"

    finally:
        process.stdout.close()
        process.stderr.close()