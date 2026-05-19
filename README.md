# 🇪🇨 Evolución Digital en el Ecuador — Chatbot IA

Línea de tiempo interactiva sobre la legislación digital ecuatoriana, con chatbot inteligente impulsado por **Groq (LLaMA 3)** y backend **FastAPI**.

---

## 📁 Estructura del Proyecto

```
project/
│
├── backend/
│   ├── main.py                  ← Servidor FastAPI (endpoint /chat)
│   ├── services/
│   │   └── groq_service.py      ← Integración con API de Groq + Prompt Engineering
│   ├── utils/
│   │   └── html_parser.py       ← Parser BeautifulSoup + chunking inteligente
│   ├── .env.example             ← Plantilla de variables de entorno
│   └── requirements.txt         ← Dependencias Python
│
├── frontend/
│   ├── index.html               ← Página principal (línea de tiempo + chatbot)
│   ├── styles.css               ← Todos los estilos (timeline + chatbot)
│   └── chatbot.js               ← Lógica del chatbot (UI + comunicación API)
│
└── README.md
```

---

## ⚙️ Requisitos Previos

- Python 3.10 o superior
- Una API Key de Groq → [console.groq.com](https://console.groq.com)

---

## 🚀 Instalación y Ejecución

### 1. Crear y activar entorno virtual

```bash
# Desde la raíz del proyecto (carpeta project/)
python -m venv venv

# Activar en macOS / Linux
source venv/bin/activate

# Activar en Windows
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configurar API Key

```bash
# Copiar la plantilla
cp .env.example .env

# Editar .env y pegar tu API Key de Groq
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

### 4. Iniciar el servidor FastAPI

```bash
# Desde la carpeta backend/
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verás:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 5. Abrir el frontend

Abre directamente en el navegador:
```
project/frontend/index.html
```

O, si prefieres un servidor local simple:
```bash
cd frontend
python -m http.server 5500
# Luego abre: http://localhost:5500
```

---

## 🔌 Endpoints de la API

| Método | Endpoint    | Descripción                              |
|--------|-------------|------------------------------------------|
| GET    | `/`         | Health check                             |
| POST   | `/chat`     | Enviar pregunta al chatbot               |
| GET    | `/context`  | Ver chunks extraídos del HTML (debug)    |
| GET    | `/docs`     | Documentación interactiva Swagger UI     |

### Ejemplo de uso

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Ecuador está preparado para un gobierno electrónico?"}'
```

---

## 🧠 Cómo funciona el chatbot

```
Usuario escribe pregunta
        ↓
chatbot.js → POST /chat { message }
        ↓
html_parser.py extrae chunks relevantes del HTML
        ↓
groq_service.py construye: System Prompt + Contexto + Pregunta
        ↓
Groq LLaMA 3 genera respuesta
        ↓
FastAPI retorna { response }
        ↓
chatbot.js muestra en la UI
```

---

## 🔒 Seguridad

- La API Key nunca sale del backend (`.env`)
- El `.env` está en `.gitignore` por defecto
- El input del usuario tiene límite de 500 caracteres
- Timeout de 25s en el frontend y 20s en el backend
- CORS configurado (restringir en producción)

---

## 📝 Variables de Entorno

| Variable       | Descripción                    | Requerida |
|----------------|--------------------------------|-----------|
| `GROQ_API_KEY` | API Key de Groq                | ✅ Sí     |

---

## 🤖 Modelo de IA

- **Proveedor**: Groq
- **Modelo**: `llama3-8b-8192`
- **Temperatura**: 0.3 (respuestas precisas y deterministas)
- **Max tokens**: 600

---

## ❓ Preguntas sugeridas

- ¿Ecuador está preparado para un gobierno electrónico?
- ¿Qué ley protege mis datos personales?
- ¿Cuál fue la primera ley digital del Ecuador?
- ¿Cómo ayuda la cédula digital a los ciudadanos?
- ¿Qué es el Código INGENIOS?
- ¿Qué cambió con la Ley de Ciberseguridad de 2026?
