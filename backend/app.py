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

# ===== CONFIG =====
STM_LIMIT = 8               # short-term memory limit
LTM_MAX_TOKENS = 250        # panjang ringkasan long-term
MAX_RESPONSE_TOKENS = 512


def summarize_to_long_term(old_messages):
    """Ringkas pesan lama menjadi memori jangka panjang"""
    summary_prompt = [
        {
            "role": "system",
            "content": "Ringkas percakapan berikut menjadi fakta teknis penting yang perlu diingat jangka panjang."
        }
    ] + old_messages

    payload = {
        "model": "local-model",
        "messages": summary_prompt,
        "temperature": 0.3,
        "max_tokens": LTM_MAX_TOKENS,
        "stream": False
    }

    try:
        r = requests.post(LLAMA_URL, json=payload, timeout=120)
        result = r.json()
        summary_text = result["choices"][0]["message"]["content"]

        return {
            "role": "system",
            "content": f"Memori Jangka Panjang:\n{summary_text}"
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

    # ===== PISAHKAN LTM & STM =====
    long_term = []
    short_term = []

    for msg in history:
        if "Memori Jangka Panjang:" in msg.get("content", ""):
            long_term = [msg]  # hanya simpan 1 LTM aktif
        else:
            short_term.append(msg)

    # ===== AUTO RINGKAS STM LAMA =====
    if len(short_term) > STM_LIMIT:
        old_part = short_term[:-STM_LIMIT]
        short_term = short_term[-STM_LIMIT:]

        summary = summarize_to_long_term(old_part)
        if summary:
            long_term = [summary]

    # ===== GABUNG FINAL MEMORY =====
    final_memory = long_term + short_term

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + final_memory + [
        {"role": "user", "content": user_message}
    ]

    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": 0.5,
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