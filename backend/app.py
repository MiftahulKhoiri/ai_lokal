from flask import Flask, render_template, request, Response
import requests
import json
import time
from backend.memory import get_memory, add_to_memory

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

LLAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"

SYSTEM_PROMPT = """Nama kamu adalah AIRA.
AI rumah pribadi.
Jawaban teknis, ringkas, langsung ke inti.
"""

# ===== OPTIMIZED CONFIG =====
STM_LIMIT = 4               # lebih kecil = context lebih ringan
MAX_RESPONSE_TOKENS = 256   # kurangi output token
REQUEST_TIMEOUT = 120


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream", methods=["POST"])
def stream():
    start_time = time.time()

    user_message = request.json.get("message", "")
    history = get_memory()

    # ===== HARD TRIM STM (TANPA RINGKAS) =====
    short_term = history[-STM_LIMIT:] if history else []

    # ===== FINAL CONTEXT =====
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + short_term + [
        {"role": "user", "content": user_message}
    ]

    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": 0.4,      # lebih rendah = lebih cepat stabil
        "max_tokens": MAX_RESPONSE_TOKENS,
        "stream": True
    }

    def generate():
        full_reply = ""

        try:
            with requests.post(
                LLAMA_URL,
                json=payload,
                stream=True,
                timeout=REQUEST_TIMEOUT
            ) as r:

                for line in r.iter_lines():
                    if not line:
                        continue

                    decoded = line.decode("utf-8")

                    if not decoded.startswith("data: "):
                        continue

                    data = decoded[6:]

                    if data == "[DONE]":
                        break

                    try:
                        json_data = json.loads(data)
                        delta = json_data["choices"][0]["delta"]
                        content = delta.get("content")

                        if content:
                            full_reply += content
                            yield content

                    except (json.JSONDecodeError, KeyError):
                        continue

        except requests.exceptions.RequestException:
            yield "⚠ Model timeout atau tidak merespon."

        finally:
            if full_reply.strip():
                add_to_memory(user_message, full_reply)

            print("Durasi respon:", round(time.time() - start_time, 2), "detik")

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

