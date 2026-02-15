from flask import Flask, render_template, request, Response
import requests
import json
from backend.memory import get_memory, add_to_memory

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

LLAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"

SYSTEM_PROMPT = """Nama kamu adalah AIRA.
Kamu adalah AI rumah pribadi.
Jawaban harus teknis, ringkas, dan tidak bertele-tele.
"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream", methods=["POST"])
def stream():
    user_message = request.json.get("message", "")

    history = get_memory()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + history + [
        {"role": "user", "content": user_message}
    ]

    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": 0.7,
        "stream": True
    }

    def generate():
        full_reply = ""

        try:
            with requests.post(
                LLAMA_URL,
                json=payload,
                stream=True,
                timeout=300
            ) as r:

                for line in r.iter_lines():
                    if not line:
                        continue

                    decoded = line.decode("utf-8")

                    if decoded.startswith("data: "):
                        data = decoded[6:]

                        if data == "[DONE]":
                            break

                        try:
                            json_data = json.loads(data)
                            delta = json_data["choices"][0]["delta"]
                            content = delta.get("content", "")

                            if content:
                                full_reply += content
                                yield content

                        except (json.JSONDecodeError, KeyError):
                            continue

        finally:
            if full_reply:
                add_to_memory(user_message, full_reply)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )