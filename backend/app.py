from flask import Flask, render_template, request, Response
from llm import stream_response
from memory import get_memory, add_to_memory

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream", methods=["POST"])
def stream():
    user_message = request.json["message"]
    history = get_memory()

    def generate():
        full_reply = ""

        for chunk in stream_response(user_message, history):
            full_reply += chunk
            yield chunk

        # Simpan ke memory setelah selesai
        add_to_memory(user_message, full_reply)

    return Response(generate(), mimetype="text/plain")