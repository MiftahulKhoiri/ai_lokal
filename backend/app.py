from flask import Flask, render_template, request, Response
import requests
import json

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

LLAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"

SYSTEM_PROMPT = "Anda adalah asisten pribadi lokal. Jawaban harus teknis dan ringkas."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream", methods=["POST"])
def stream():
    user_message = request.json["message"]

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "stream": True
    }

    def generate():
        with requests.post(
            LLAMA_URL,
            json=payload,
            stream=True
        ) as r:

            for line in r.iter_lines():
                if line:
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
                                yield content
                        except:
                            continue

    return Response(generate(), mimetype="text/plain")