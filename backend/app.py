import os
import json
import time
import uuid
import logging
from typing import Dict, Generator

import requests
from flask import Flask, render_template, request, Response, jsonify

from backend.memory import (
    get_memory,
    add_to_memory,
    load_memory
)

# =============================
# CONFIG
# =============================

MODEL_ENDPOINTS = {
    "3b": os.getenv("MODEL_3B_URL", "http://127.0.0.1:8080/v1/chat/completions"),
    "7b": os.getenv("MODEL_7B_URL", "http://127.0.0.1:8081/v1/chat/completions"),
}

SYSTEM_PROMPT = """Nama kamu adalah AIRA.
AI rumah pribadi.
Jawaban teknis, ringkas, langsung ke inti.
"""

MAX_RESPONSE_TOKENS = 256
REQUEST_TIMEOUT = (5, 120)
DEFAULT_MODEL = "3b"

# =============================
# APP INIT
# =============================

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

load_memory()

# =============================
# LOGGING
# =============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("AIRA")

# =============================
# UTILITIES
# =============================

def estimate_complexity(text: str) -> str:
    score = 0
    text_lower = text.lower()

    if len(text) > 200:
        score += 1

    keywords = [
        "analisa", "bandingkan", "optimasi",
        "arsitektur", "debug", "kenapa",
        "mendalam", "refactor"
    ]

    if any(k in text_lower for k in keywords):
        score += 1

    if "```" in text or "def " in text:
        score += 1

    return "7b" if score >= 2 else "3b"


def build_payload(messages: list) -> Dict:
    return {
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": MAX_RESPONSE_TOKENS,
        "stream": True
    }


def call_model_stream(url: str, payload: Dict) -> Generator[str, None, None]:
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
                    yield content
            except Exception:
                continue


def build_messages(user_message: str, model_choice: str):
    STM_LIMIT = 6 if model_choice == "7b" else 4
    history = get_memory(model_choice)
    short_term = history[-STM_LIMIT:] if history else []

    return (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + short_term
        + [{"role": "user", "content": user_message}]
    )

# =============================
# ROUTES
# =============================

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
        except requests.RequestException:
            status[model] = False

    return jsonify(status)


@app.route("/stream", methods=["POST"])
def stream():
    request_id = str(uuid.uuid4())
    start_time = time.time()

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    manual_model = data.get("model")

    if not user_message:
        return Response("Pesan kosong", status=400)

    # Smart routing
    if manual_model in MODEL_ENDPOINTS:
        model_choice = manual_model
    else:
        model_choice = estimate_complexity(user_message)

    logger.info(f"[{request_id}] Incoming | Model: {model_choice}")

    messages = build_messages(user_message, model_choice)
    payload = build_payload(messages)

    def generate():
        full_reply = ""
        used_model = model_choice

        try:
            yield from call_model_stream(
                MODEL_ENDPOINTS[model_choice],
                payload
            )

        except requests.RequestException as e:
            logger.warning(f"[{request_id}] {model_choice} failed: {e}")

            # fallback 7B → 3B
            if model_choice == "7b":
                try:
                    used_model = "3b"
                    yield "\n\n⚠ Fallback ke 3B...\n\n"

                    yield from call_model_stream(
                        MODEL_ENDPOINTS["3b"],
                        payload
                    )

                except Exception as fallback_error:
                    logger.error(f"[{request_id}] Fallback failed: {fallback_error}")
                    yield "⚠ Semua model gagal."
            else:
                yield "⚠ Model tidak merespon."

        finally:
            duration = round(time.time() - start_time, 2)

            if full_reply.strip():
                add_to_memory(user_message, full_reply, used_model)

            logger.info(
                f"[{request_id}] Done | Model: {used_model} | {duration}s"
            )

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)