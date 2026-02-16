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

# =========================
# MODEL ENDPOINTS
# =========================

MODEL_ENDPOINTS = {
    "3b": "http://127.0.0.1:8080/v1/chat/completions",
    "7b": "http://127.0.0.1:8081/v1/chat/completions"
}

SYSTEM_PROMPT = """Nama kamu adalah AIRA.
AI rumah pribadi.
Jawaban teknis, ringkas, langsung ke inti.
"""

# ===== CONFIG =====
STM_LIMIT = 4
MAX_RESPONSE_TOKENS = 256
REQUEST_TIMEOUT = 120


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream", methods=["POST"])
def stream():
    start_time = time.time()

    user_message = request.json.get("message", "")
    model_choice = request.json.get("model", "3b")

    if model_choice not in MODEL_ENDPOINTS:
        return Response("Model tidak valid", status=400)

    LLAMA_URL = MODEL_ENDPOINTS[model_choice]

    history = get_memory()

    # ===== HARD TRIM STM =====
    short_term = history[-STM_LIMIT:] if history else []

    # ===== FINAL CONTEXT =====
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + short_term + [
        {"role": "user", "content": user_message}
    ]

    payload = {
        "messages": messages,
        "temperature": 0.4,
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

            print(
                f"[MODEL: {model_choice.upper()}] Durasi:",
                round(time.time() - start_time, 2),
                "detik"
            )

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )