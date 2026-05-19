"""
main.py — Backend Flask para Evolución Digital Ecuador
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pathlib
import asyncio

from services.groq_service import GroqService
from utils.html_parser import HTMLParser

# ─── Rutas ────────────────────────────────────────────────────
BASE_DIR     = pathlib.Path(__file__).parent.parent
HTML_PATH    = BASE_DIR / "frontend" / "index.html"

# ─── App ──────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─── Servicios ────────────────────────────────────────────────
html_parser  = HTMLParser(html_path=str(HTML_PATH))
groq_service = GroqService()

# ─── Endpoints ────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "ok", "message": "Chatbot API activa"})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "El campo message es requerido"}), 400

    user_message = data["message"].strip()

    if not user_message:
        return jsonify({"error": "El mensaje no puede estar vacío"}), 400

    if len(user_message) > 500:
        return jsonify({"error": "Mensaje demasiado largo (máx. 500 caracteres)"}), 400

    context_chunks = html_parser.get_relevant_chunks(query=user_message)

    # Flask es síncrono — ejecutar la corrutina así
    response_text = asyncio.run(
        groq_service.generate_response(
            user_message=user_message,
            context_chunks=context_chunks,
        )
    )

    return jsonify({"response": response_text, "context_used": bool(context_chunks)})


@app.route("/context", methods=["GET"])
def get_context():
    chunks = html_parser.get_all_chunks()
    return jsonify({"total_chunks": len(chunks), "chunks": chunks})


if __name__ == "__main__":
    app.run(debug=False)