import os
import json
import time
import uuid
import logging
import threading
from typing import Dict, Generator, List, Optional, Tuple

import requests
from flask import Flask, render_template, request, Response, jsonify, stream_with_context

from backend.memory import get_memory, add_to_memory, load_memory
from backend.agent import Agent
from backend.config_loader import load_all_configs
from backend.dev_tools import *


# =============================
# CONFIG
# =============================

configs = load_all_configs()

SYSTEM_PROMPT = configs.get("system_prompt") or "Kamu adalah AI agent."
AI_CONFIG = configs.get("ai_config", {})
USER_PROFILE = configs.get("user_profile", {})
AGENT_CONFIG = configs.get("agent_config", {})

MODEL_ENDPOINT = os.getenv(
    "MODEL_URL",
    "http://127.0.0.1:8081/v1/chat/completions"
)

MAX_TOKENS = AI_CONFIG.get("max_tokens", 256)
TEMPERATURE = AI_CONFIG.get("temperature", 0.4)
STM_LIMIT = AI_CONFIG.get("short_term_limit", 6)
WORKSPACE_ROOT = AI_CONFIG.get("workspace_root", ".")

REQUEST_TIMEOUT = (10, 300)


# =============================
# APP
# =============================

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False


# =============================
# MEMORY
# =============================

load_memory()
memory_lock = threading.Lock()


# =============================
# AGENT
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
# TOOL REGISTRY
# =============================

TOOLS = {

    "get_system_status": agent.get_system_status,
    "get_current_time": agent.get_current_time,

    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "delete_file": delete_file,
    "list_files": list_files,
    "make_directory": make_directory,
    "search_text": search_text,
    "file_info": file_info,
    "run_python": run_python,
    "run_shell": run_shell,
    "project_tree": project_tree
}


# =============================
# UTILITIES
# =============================

def build_payload(messages: List[Dict]) -> Dict:
    return {
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "stream": True
    }


def build_messages(user_message: str) -> List[Dict]:

    history = get_memory()
    short_term = history[-(STM_LIMIT * 2):] if history else []

    tool_list = "\n".join([f"- {t}" for t in TOOLS.keys()])

    system_block = f"""
{SYSTEM_PROMPT}

Kamu adalah Autonomous AI Agent.

Gunakan format berikut:

Thought: pemikiran kamu

Jika membutuhkan tool gunakan:

ACTION: nama_tool argumen

Contoh:

ACTION: read_file main.py
ACTION: write_file hello.py | print("hello")
ACTION: run_python hello.py

Jika sudah selesai gunakan:

FINAL: jawaban

TOOLS YANG TERSEDIA:

{tool_list}

User Profile:
{json.dumps(USER_PROFILE, indent=2)}
"""

    messages = [{"role": "system", "content": system_block}]
    messages.extend(short_term)
    messages.append({"role": "user", "content": user_message})

    return messages


# =============================
# STREAM MODEL
# =============================

def call_model_stream(url: str, payload: Dict) -> Generator[str, None, None]:

    try:

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

    except Exception as e:
        logger.error(f"Model error: {e}")
        yield "\n⚠ Model tidak merespon.\n"


# =============================
# ACTION PARSER
# =============================

def parse_action(text: str) -> Tuple[Optional[str], Optional[str]]:

    # format ACTION
    if "ACTION:" in text:

        try:

            line = text.split("ACTION:")[1].strip()
            parts = line.split(" ", 1)

            tool = parts[0]
            args = ""

            if len(parts) > 1:
                args = parts[1]

            return tool, args

        except:
            pass

    # format JSON
    try:

        data = json.loads(text)

        if "action" in data:

            tool = data["action"]

            params = data.get("params", {})

            if isinstance(params, dict):
                args = "|".join(str(v) for v in params.values())
            else:
                args = str(params)

            return tool, args

    except:
        pass

    return None, None


def detect_final(text: str) -> Optional[str]:

    if "FINAL:" not in text:
        return None

    return text.split("FINAL:")[1].strip()


# =============================
# TOOL EXECUTOR
# =============================

def run_tool(tool_name: str, args: str) -> str:

    tool = TOOLS.get(tool_name)

    if not tool:
        return f"Tool '{tool_name}' tidak ditemukan."

    try:

        if not args:
            return tool()

        params = args.split("|")
        params = [p.strip() for p in params]

        return tool(*params)

    except Exception as e:
        return f"Tool error: {e}"


# =============================
# ROUTES
# =============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():

    try:

        base = MODEL_ENDPOINT.split("/v1/")[0]
        r = requests.get(base + "/health", timeout=2)

        return jsonify({"model": r.status_code == 200})

    except requests.RequestException:
        return jsonify({"model": False})


# =============================
# STREAM
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

    def generate():

        messages_local = build_messages(user_message)

        max_steps = 6
        step = 0
        final_answer = ""

        try:

            while step < max_steps:

                payload = build_payload(messages_local)

                current_reply = ""

                for chunk in call_model_stream(MODEL_ENDPOINT, payload):
                    current_reply += chunk
                    yield f"data: {chunk}\n\n"

                current_reply = current_reply.strip()

                if not current_reply:
                    break

                final = detect_final(current_reply)

                if final:
                    final_answer = final
                    yield "data: [DONE]\n\n"
                    break

                tool, args = parse_action(current_reply)

                if not tool:
                    final_answer = current_reply
                    yield "data: [DONE]\n\n"
                    break

                observation = run_tool(tool, args)

                messages_local.append({
                    "role": "assistant",
                    "content": current_reply
                })

                messages_local.append({
                    "role": "system",
                    "content": f"OBSERVATION:\n{observation}"
                })

                logger.info(f"[{request_id}] Tool executed: {tool}")

                step += 1

            else:
                yield "data: ⚠ Batas reasoning tercapai\n\n"

        except Exception as e:

            logger.error(f"[{request_id}] Error: {e}")
            yield "data: ⚠ Server error\n\n"

        finally:

            duration = round(time.time() - start_time, 2)

            if final_answer:
                with memory_lock:
                    add_to_memory(user_message, final_answer)

            logger.info(f"[{request_id}] Done {duration}s")

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
# RUN
# =============================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )