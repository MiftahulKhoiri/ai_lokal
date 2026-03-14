import os
import json
import time
import uuid
import logging
import threading
from typing import Dict, Generator, List

import requests
from flask import (
    Flask,
    render_template,
    request,
    Response,
    jsonify,
    stream_with_context
)

from backend.memory import (
    get_memory,
    add_to_memory,
    load_memory
)

from backend.agent import Agent
from backend.config_loader import load_all_configs


# =============================
# CONFIG LOADER
# =============================

configs = load_all_configs()

SYSTEM_PROMPT = configs.get("system_prompt") or "Kamu adalah AI."
AI_CONFIG = configs.get("ai_config", {})
USER_PROFILE = configs.get("user_profile", {})
REVIEW_CONFIG = configs.get("review_config", {})
AGENT_CONFIG = configs.get("agent_config", {})

MODEL_ENDPOINT = os.getenv(
    "MODEL_URL",
    "http://127.0.0.1:8081/v1/chat/completions"
)

MAX_RESPONSE_TOKENS = AI_CONFIG.get("max_tokens", 256)
TEMPERATURE = AI_CONFIG.get("temperature", 0.4)
STM_LIMIT = AI_CONFIG.get("short_term_limit", 6)
WORKSPACE_ROOT = AI_CONFIG.get("workspace_root", ".")

REQUEST_TIMEOUT = (10, 300)


# =============================
# APP INIT
# =============================

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False


# =============================
# LOAD MEMORY
# =============================

load_memory()
memory_lock = threading.Lock()


# =============================
# AGENT INIT
# =============================

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
# TOOL KEYWORDS
# =============================

TOOL_KEYWORDS = {
    ("jam", "hari", "tanggal"): "time",
    ("cpu", "ram", "status sistem"): "system"
}


# =============================
# UTILITIES
# =============================

def build_payload(messages: List[Dict]) -> Dict:
    return {
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_RESPONSE_TOKENS,
        "stream": True
    }


def build_messages(user_message: str) -> List[Dict]:

    history = get_memory()

    short_term = history[-(STM_LIMIT * 2):] if history else []

    system_block = f"""
{SYSTEM_PROMPT}

=== USER PROFILE ===
{json.dumps(USER_PROFILE, indent=2)}
"""

    messages = [{"role": "system", "content": system_block}]
    messages.extend(short_term)
    messages.append({"role": "user", "content": user_message})

    return messages


def call_model_stream(url: str, payload: Dict) -> Generator[str, None, None]:

    try:

        with requests.post(
            url,
            json=payload,
            stream=True,
            timeout=REQUEST_TIMEOUT
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines():

                if not line:
                    continue

                decoded = line.decode("utf-8")

                if not decoded.startswith("data:"):
                    continue

                data = decoded[5:].strip()

                if data == "[DONE]":
                    break

                try:

                    parsed = json.loads(data)

                    choices = parsed.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    content = delta.get("content")

                    if content:
                        yield content

                except json.JSONDecodeError:
                    continue

    except requests.RequestException as e:
        logger.error(f"Model connection error: {e}")
        yield "\n⚠ Model tidak merespon.\n"


def detect_direct_tool(user_message: str):

    msg = user_message.lower()

    for keys, tool in TOOL_KEYWORDS.items():

        if any(k in msg for k in keys):

            if tool == "time":
                return agent.get_current_time()

            if tool == "system":
                return agent.get_system_status()

    return None


# =============================
# ROUTES
# =============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():

    try:

        base_url = MODEL_ENDPOINT.split("/v1/")[0]
        health_url = base_url + "/health"

        r = requests.get(health_url, timeout=2)

        return jsonify({
            "model": r.status_code == 200
        })

    except requests.RequestException:

        return jsonify({
            "model": False
        })


# =============================
# STREAM ROUTE
# =============================

@app.route("/stream", methods=["POST"])
def stream():

    request_id = str(uuid.uuid4())
    start_time = time.time()

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return Response("Pesan kosong", status=400)

    logger.info(f"[{request_id}] User: {user_message}")

    # =============================
    # DIRECT TOOL EXECUTION
    # =============================

    direct_tool = detect_direct_tool(user_message)

    if direct_tool:
        logger.info(f"[{request_id}] Direct tool executed")
        return Response(direct_tool, mimetype="text/plain")

    # =============================
    # STREAM GENERATOR
    # =============================

    def generate():

        max_steps = 2
        step = 0
        final_reply = ""

        messages_local = build_messages(user_message)

        try:

            while step < max_steps:

                payload = build_payload(messages_local)

                current_reply = ""

                for chunk in call_model_stream(MODEL_ENDPOINT, payload):

                    current_reply += chunk
                    yield f"data: {chunk}\n\n"

                current_reply = current_reply.strip()

                if not current_reply:
                    yield "data: ⚠ Model tidak menghasilkan respon.\n\n"
                    break

                action_result = agent.execute_action(current_reply)

                if action_result is None:

                    final_reply = current_reply
                    yield "data: [DONE]\n\n"
                    break

                messages_local.append({
                    "role": "assistant",
                    "content": current_reply
                })

                messages_local.append({
                    "role": "system",
                    "content": f"Tool Result:\n{action_result}"
                })

                logger.info(f"[{request_id}] Tool executed step {step+1}")

                step += 1

            else:

                yield "data: ⚠ Batas reasoning tercapai.\n\n"

        except Exception as e:

            logger.error(f"[{request_id}] Error: {e}")
            yield "data: ⚠ Terjadi kesalahan server.\n\n"

        finally:

            duration = round(time.time() - start_time, 2)

            if final_reply:

                with memory_lock:
                    add_to_memory(user_message, final_reply)

            logger.info(f"[{request_id}] Done in {duration}s")

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =============================
# RUN SERVER
# =============================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )