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

from backend.agent import Agent
from backend.config_loader import load_all_configs

# =============================
# LOAD CONFIG FROM FILES
# =============================

configs = load_all_configs()

SYSTEM_PROMPT = configs["system_prompt"] or "Kamu adalah AI."
AI_CONFIG = configs["ai_config"]
USER_PROFILE = configs["user_profile"]

MODEL_ENDPOINT = os.getenv(
    "MODEL_URL",
    "http://127.0.0.1:8081/v1/chat/completions"
)

MAX_RESPONSE_TOKENS = AI_CONFIG.get("max_tokens", 256)
TEMPERATURE = AI_CONFIG.get("temperature", 0.4)
REQUEST_TIMEOUT = (5, 120)
STM_LIMIT = AI_CONFIG.get("short_term_limit", 6)

# Load review template
DATA_DIR = "data"
REVIEW_FILE = os.path.join(DATA_DIR, "file_review.json")

if not os.path.exists(REVIEW_FILE):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "review_template": (
                "Berikut isi file {filename}.\n"
                "Lakukan review teknis:\n"
                "- Jelaskan fungsi utama\n"
                "- Identifikasi bug\n"
                "- Berikan saran refactor\n"
                "- Nilai kualitas struktur kode\n\n"
                "Isi file:\n{content}"
            )
        }, f, indent=4)

with open(REVIEW_FILE, "r", encoding="utf-8") as f:
    REVIEW_CONFIG = json.load(f)

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
agent = Agent()

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

def build_payload(messages: list) -> Dict:
    return {
        "messages": messages,
        "temperature": TEMPERATURE,
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


def build_messages(user_message: str):
    history = get_memory()
    short_term = history[-STM_LIMIT:] if history else []

    system_block = f"""
{SYSTEM_PROMPT}

=== USER PROFILE ===
{json.dumps(USER_PROFILE, indent=2)}
"""

    return (
        [{"role": "system", "content": system_block}]
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
    try:
        health_url = MODEL_ENDPOINT.replace("/v1/chat/completions", "/health")
        r = requests.get(health_url, timeout=2)
        return jsonify({"model": r.status_code == 200})
    except requests.RequestException:
        return jsonify({"model": False})


@app.route("/stream", methods=["POST"])
def stream():
    request_id = str(uuid.uuid4())
    start_time = time.time()

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return Response("Pesan kosong", status=400)

    # =========================
    # AGENT LAYER
    # =========================
    agent_response = agent.handle(user_message)

    if isinstance(agent_response, dict):

        if agent_response.get("action") == "analyze_file":
            filename = agent_response.get("filename")

            try:
                file_content = agent.read_file(filename)

                review_template = REVIEW_CONFIG.get("review_template", "")
                review_prompt = review_template.format(
                    filename=filename,
                    content=file_content
                )

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": review_prompt}
                ]

                payload = build_payload(messages)

                def generate_review():
                    for chunk in call_model_stream(
                        MODEL_ENDPOINT,
                        payload
                    ):
                        yield chunk

                return Response(
                    generate_review(),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no"
                    }
                )

            except Exception as e:
                return Response(f"Gagal analisa file: {e}", status=500)

    if isinstance(agent_response, str):
        logger.info(f"[{request_id}] Agent executed")
        return Response(agent_response, mimetype="text/plain")

    # =========================
    # NORMAL FLOW
    # =========================

    logger.info(f"[{request_id}] Incoming request")

    messages = build_messages(user_message)
    payload = build_payload(messages)

    def generate():
        full_reply = ""

        try:
            for chunk in call_model_stream(
                MODEL_ENDPOINT,
                payload
            ):
                full_reply += chunk
                yield chunk

        except requests.RequestException as e:
            logger.error(f"[{request_id}] Model error: {e}")
            yield "⚠ Model tidak merespon."

        finally:
            duration = round(time.time() - start_time, 2)

            if full_reply.strip():
                add_to_memory(user_message, full_reply)

            logger.info(
                f"[{request_id}] Done | {duration}s"
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