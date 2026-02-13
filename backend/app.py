from flask import Flask, render_template, request, jsonify
from llm import generate_response
from memory import add_to_memory, get_memory

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    history = get_memory()

    response = generate_response(user_message, history)

    add_to_memory(user_message, response)

    return jsonify({"reply": response})
