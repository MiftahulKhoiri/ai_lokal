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
# LOAD CONFIG
# =============================

configs = load_all_configs()

SYSTEM_PROMPT = configs["system_prompt"] or "Kamu adalah AI."
AI_CONFIG = configs["ai_config"]
USER_PROFILE = configs["user_profile"]
REVIEW_CONFIG = configs["review_config"]
AGENT_CONFIG = configs["agent_config"]

MODEL_ENDPOINT = os.getenv(
    "MODEL_URL",
    "http://127.0.0.1:8081/v1/chat/completions"
)

MAX_RESPONSE_TOKENS = AI_CONFIG.get("max_tokens", 256)
TEMPERATURE = AI_CONFIG.get("temperature", 0.4)
REQUEST_TIMEOUT = (5, 120)
STM_LIMIT = AI_CONFIG.get("short_term_limit", 6)
WORKSPACE_ROOT = AI_CONFIG.get("workspace_root", ".")

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

agent = Agent(
    agent_config=AGENT_CONFIG,
    workspace_root=WORKSPACE_ROOT
)

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

    logger.info(f"[{request_id}] Incoming request")

    # =========================
    # FAST DIRECT TOOL ROUTING
    # =========================
    lower_msg = user_message.lower()

    if any(k in lower_msg for k in ["jam", "hari", "tanggal"]):
        result = agent.get_current_time()
        logger.info(f"[{request_id}] Direct time tool executed")
        return Response(result, mimetype="text/plain")

    if any(k in lower_msg for k in ["cpu", "ram", "status sistem"]):
        result = agent.get_system_status()
        logger.info(f"[{request_id}] Direct system tool executed")
        return Response(result, mimetype="text/plain")

    # =========================
    # NORMAL HYBRID LOOP
    # =========================

    def generate():
        max_steps = 2
        step = 0
        final_reply = ""

        messages_local = build_messages(user_message)

        try:
            while step < max_steps:

                payload = build_payload(messages_local)

                current_reply = ""

                for chunk in call_model_stream(
                    MODEL_ENDPOINT,
                    payload
                ):
                    current_reply += chunk

                current_reply = current_reply.strip()

                action_result = agent.execute_action(current_reply)

                if action_result is None:
                    final_reply = current_reply
                    yield final_reply
                    break

                messages_local.append({
                    "role": "assistant",
                    "content": current_reply
                })

                messages_local.append({
                    "role": "assistant",
                    "content": f"HASIL_TOOL:\n{action_result}"
                })

                logger.info(f"[{request_id}] Tool executed (step {step+1})")
                step += 1

            else:
                yield "⚠ Batas reasoning tercapai."

        except requests.RequestException as e:
            logger.error(f"[{request_id}] Model error: {e}")
            yield "⚠ Model tidak merespon."

        finally:
            duration = round(time.time() - start_time, 2)

            if final_reply.strip():
                add_to_memory(user_message, final_reply)

            logger.info(f"[{request_id}] Done | {duration}s")

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