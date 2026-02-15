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

MAX_HISTORY = 10
SUMMARY_TRIGGER = 12
SUMMARY_KEEP = 6
SUMMARY_MAX_TOKENS = 200


def summarize_history(history):
    summary_prompt = [
        {
            "role": "system",
            "content": "Ringkas percakapan berikut secara teknis dan padat. Simpan fakta penting, hapus basa-basi."
        }
    ] + history

    payload = {
        "model": "local-model",
        "messages": summary_prompt,
        "temperature": 0.3,
        "max_tokens": SUMMARY_MAX_TOKENS,
        "stream": False
    }

    try:
        r = requests.post(LLAMA_URL, json=payload, timeout=120)
        result = r.json()
        summary_text = result["choices"][0]["message"]["content"]

        return {
            "role": "system",
            "content": f"Ringkasan percakapan sebelumnya:\n{summary_text}"
        }

    except:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream", methods=["POST"])
def stream():
    user_message = request.json.get("message", "")
    history = get_memory()

    # ===== AUTO RINGKAS MEMORY =====
    if len(history) > SUMMARY_TRIGGER:
        old_part = history[:-SUMMARY_KEEP]
        new_part = history[-SUMMARY_KEEP:]

        summary = summarize_history(old_part)

        if summary:
            history = [summary] + new_part
        else:
            history = new_part

    # Batasi history akhir
    history = history[-MAX_HISTORY:]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + history + [
        {"role": "user", "content": user_message}
    ]

    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 512,
        "stream": True
    }

    def generate():
        full_reply = ""

        try:
            with requests.post(
                LLAMA_URL,
                json=payload,
                stream=True,
                timeout=180
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
            yield "⚠ Model tidak merespon."

        finally:
            if full_reply.strip():
                add_to_memory(user_message, full_reply)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)