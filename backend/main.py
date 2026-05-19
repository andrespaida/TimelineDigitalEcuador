"""
main.py — Punto de entrada de la API FastAPI
Evolución Digital Ecuador — Chatbot Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import os
import pathlib

from services.groq_service import GroqService
from utils.html_parser import HTMLParser

# ─── Configuración ─────────────────────────────────────────────────────────────

BASE_DIR = pathlib.Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
HTML_PATH = FRONTEND_DIR / "index.html"

app = FastAPI(
    title="Evolución Digital Ecuador — Chatbot API",
    description="Backend inteligente para chatbot sobre legislación digital ecuatoriana",
    version="1.0.0",
)

# ─── CORS (permite que el frontend local consuma la API) ───────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # En producción: restringir a dominio específico
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Servir frontend estático ──────────────────────────────────────────────────

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ─── Inicializar servicios ─────────────────────────────────────────────────────

html_parser = HTMLParser(html_path=str(HTML_PATH))
groq_service = GroqService()

# ─── Schemas ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Pregunta del usuario sobre la línea de tiempo",
    )

class ChatResponse(BaseModel):
    response: str
    context_used: bool = False   # indica si se encontró contexto relevante

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
async def root() -> dict:
    return {"status": "ok", "message": "Chatbot API activa"}


@app.post("/chat", response_model=ChatResponse, summary="Enviar mensaje al chatbot")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Recibe una pregunta del usuario, extrae contexto relevante del HTML
    y devuelve una respuesta generada por el modelo Groq.
    """
    # 1. Sanitizar input
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    # 2. Extraer fragmentos relevantes del HTML
    context_chunks = html_parser.get_relevant_chunks(query=user_message)
    has_context = bool(context_chunks)

    # 3. Generar respuesta con Groq
    response_text = await groq_service.generate_response(
        user_message=user_message,
        context_chunks=context_chunks,
    )

    return ChatResponse(response=response_text, context_used=has_context)


@app.get("/context", summary="Ver contexto extraído del HTML (debug)")
async def get_context() -> dict:
    """Endpoint de depuración: devuelve todo el contexto extraído del HTML."""
    all_chunks = html_parser.get_all_chunks()
    return {"total_chunks": len(all_chunks), "chunks": all_chunks}
