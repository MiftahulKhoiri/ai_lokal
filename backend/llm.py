import subprocess

MODEL_PATH = "../models/qwen2.5-3b-instruct-q4_k_m.gguf"
LLAMA_PATH = "/home/pi5/llama.cpp/build/bin/llama-cli"

SYSTEM_PROMPT = """Anda adalah asisten pribadi lokal.
Jawaban harus jelas, teknis, dan ringkas.
"""

def generate_response(user_input, history):
    prompt = SYSTEM_PROMPT + "\n"

    for h in history:
        prompt += f"User: {h['user']}\nAssistant: {h['assistant']}\n"

    prompt += f"User: {user_input}\nAssistant:"

    cmd = [
        LLAMA_PATH,
        "-m", MODEL_PATH,
        "-p", prompt,
        "-n", "256",
        "--temp", "0.7",
        "--ctx-size", "2048"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.split("Assistant:")[-1].strip()