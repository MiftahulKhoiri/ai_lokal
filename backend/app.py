from flask import Flask, render_template, request, Response, jsonify
import requests
import json
import time

from backend.memory import (
    get_memory,
    add_to_memory,
    load_memory
)

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Load memory saat server start
load_memory()

MODEL_ENDPOINTS = {
    "3b": "http://127.0.0.1:8080/v1/chat/completions",
    "7b": "http://127.0.0.1:8081/v1/chat/completions"
}

SYSTEM_PROMPT = """Nama kamu adalah AIRA.
AI rumah pribadi.
Jawaban teknis, ringkas, langsung ke inti.
"""

MAX_RESPONSE_TOKENS = 256
REQUEST_TIMEOUT = (5, 120)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    status = {}
    for model, url in MODEL_ENDPOINTS.items():
        try:
            health_url = url.replace("/v1/chat/completions", "/health")
            r = requests.get(health_url, timeout=2)
            status[model] = r.status_code == 200
        except:
            status[model] = False
    return jsonify(status)


@app.route("/stream", methods=["POST"])
def stream():
    start_time = time.time()

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")
    model_choice = data.get("model", "3b")

    if not user_message.strip():
        return Response("Pesan kosong", status=400)

    if model_choice not in MODEL_ENDPOINTS:
        return Response("Model tidak valid", status=400)

    STM_LIMIT = 6 if model_choice == "7b" else 4
    LLAMA_URL = MODEL_ENDPOINTS[model_choice]

    history = get_memory(model_choice)
    short_term = history[-STM_LIMIT:] if history else []

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
        used_model = model_choice

        def stream_request(url):
            nonlocal full_reply
            with requests.post(
                url,
                json=payload,
                stream=True,
                timeout=REQUEST_TIMEOUT
            ) as r:

                r.raise_for_status()

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

                    except:
                        continue

        try:
            yield from stream_request(LLAMA_URL)

        except requests.exceptions.RequestException:

            # AUTO FALLBACK 7B → 3B
            if model_choice == "7b":
                try:
                    used_model = "3b"
                    yield "\n\n⚠ 7B tidak merespon, fallback ke 3B...\n\n"
                    yield from stream_request(MODEL_ENDPOINTS["3b"])
                except:
                    yield "⚠ Semua model gagal merespon."
            else:
                yield "⚠ Model tidak merespon."

        finally:
            if full_reply.strip():
                add_to_memory(user_message, full_reply, used_model)

            print(
                f"[MODEL: {used_model.upper()}] Durasi:",
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