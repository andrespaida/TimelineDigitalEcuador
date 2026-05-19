"""
services/groq_service.py — Integración con la API de Groq
Maneja la comunicación con el LLM y el prompt engineering.
"""

import os
import httpx
from dotenv import load_dotenv
from typing import List

load_dotenv()

# ─── Constantes ───────────────────────────────────────────────────────────────

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"        # Rápido y eficiente para este caso
MAX_TOKENS   = 600
TEMPERATURE  = 0.3                        # Respuestas más deterministas y precisas
REQUEST_TIMEOUT = 20.0                    # segundos

# ─── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Eres un asistente experto ÚNICAMENTE en la evolución digital y legislación tecnológica del Ecuador.

CONTEXTO DISPONIBLE:
Tienes acceso a 7 leyes ecuatorianas: 
- 2002: Ley de Comercio Electrónico
- 2015: Ley Orgánica de Telecomunicaciones  
- 2016: Código INGENIOS
- 2018: Ley de Optimización de Trámites
- 2021: Ley de Protección de Datos Personales
- 2023: Ley de Transformación Digital y Audiovisual
- 2026: Ley de Ciberseguridad

REGLAS ABSOLUTAS — NUNCA las violes:
1. USA SOLO la información del CONTEXTO que se te proporciona en cada mensaje.
2. NUNCA inventes leyes, fechas, artículos o datos que no estén en el contexto.
3. Si la pregunta no tiene respuesta en el contexto, responde EXACTAMENTE:
   "No encontré información sobre eso en la línea de tiempo."
4. SIEMPRE cita el año y nombre de la ley cuando la menciones.
5. Responde en español, de forma clara y estructurada.
6. Máximo 200 palabras por respuesta salvo que se pida más detalle.

PARA LA PREGUNTA SOBRE GOBIERNO ELECTRÓNICO:
Analiza TODAS las leyes del contexto y argumenta si Ecuador está o no preparado,
citando cada ley como evidencia concreta. Sé balanceado: menciona avances y pendientes.
""".strip()


# ─── Servicio ─────────────────────────────────────────────────────────────────

class GroqService:
    """
    Servicio que gestiona las llamadas a la API de Groq.
    """

    def __init__(self) -> None:
        self.api_key: str = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError(
                "GROQ_API_KEY no está definida. Verifica tu archivo .env"
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_response(
        self,
        user_message: str,
        context_chunks: List[str],
    ) -> str:
        """
        Genera una respuesta usando el modelo Groq con el contexto extraído.

        Args:
            user_message: Pregunta del usuario.
            context_chunks: Fragmentos de texto relevantes extraídos del HTML.

        Returns:
            Texto de respuesta del modelo.
        """
        # Construir el bloque de contexto
        if context_chunks:
            context_block = "\n\n---\n\n".join(context_chunks)
            context_section = f"CONTEXTO DE LA LÍNEA DE TIEMPO:\n\n{context_block}"
        else:
            context_section = (
                "CONTEXTO DE LA LÍNEA DE TIEMPO:\n\n"
                "[No se encontraron fragmentos relevantes para esta pregunta]"
            )

        # Mensaje de usuario con contexto embebido
        full_user_message = (
            f"{context_section}\n\n"
            f"INSTRUCCIÓN: Responde la siguiente pregunta BASÁNDOTE EXCLUSIVAMENTE "
            f"en el contexto de leyes ecuatorianas proporcionado arriba. "
            f"No uses conocimiento externo.\n\n"
            f"PREGUNTA: {user_message}"
        )

        payload = {
            "model": GROQ_MODEL,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": full_user_message},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    GROQ_API_URL,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

        except httpx.TimeoutException:
            return "El servicio tardó demasiado en responder. Intenta de nuevo."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return "Error de autenticación con la API. Verifica tu GROQ_API_KEY."
            return f"Error al contactar el servicio de IA ({e.response.status_code})."
        except Exception as e:
            return "Ocurrió un error inesperado al generar la respuesta."
