/**
 * chatbot.js — Lógica del chatbot para Evolución Digital Ecuador
 * Maneja UI, comunicación con el backend FastAPI y accesibilidad.
 */

(() => {
    "use strict";

    // ─── Configuración ─────────────────────────────────────────────────────────

    const API_URL = "https://ecuador-digital-backend.onrender.com/chat";
    const MAX_MSG_LEN  = 500;   // Sincronizado con el backend
    const SUGGESTIONS  = [
        "¿Ecuador está preparado para un gobierno electrónico?",
        "¿Qué ley protege mis datos personales?",
        "¿Cuál fue la primera ley digital del Ecuador?",
        "¿Cómo ayuda la cédula digital?",
    ];

    // ─── Elementos DOM ─────────────────────────────────────────────────────────

    const toggle     = document.getElementById("chatbot-toggle");
    const window_    = document.getElementById("chatbot-window");
    const messages   = document.getElementById("chat-messages");
    const input      = document.getElementById("chat-input");
    const sendBtn    = document.getElementById("chat-send");
    const suggestBox = document.getElementById("suggestions-box");

    // ─── Estado ────────────────────────────────────────────────────────────────

    let isOpen      = false;
    let isLoading   = false;
    let initialized = false;   // Solo mostrar bienvenida una vez

    // ─── Toggle ventana ────────────────────────────────────────────────────────

    toggle.addEventListener("click", () => {
        isOpen = !isOpen;

        toggle.classList.toggle("open", isOpen);
        window_.classList.toggle("open", isOpen);

        if (isOpen) {
            if (!initialized) {
                showWelcome();
                renderSuggestions();
                initialized = true;
            }
            setTimeout(() => input.focus(), 300);
        }
    });

    // ─── Bienvenida ────────────────────────────────────────────────────────────

    function showWelcome() {
        addMessage(
            "bot",
            "¡Hola! Soy el asistente de la Línea de Tiempo Digital del Ecuador 🇪🇨\n\n" +
            "Puedo responder preguntas sobre las leyes y hitos de la evolución digital ecuatoriana. " +
            "¿En qué te puedo ayudar?"
        );
    }

    // ─── Sugerencias rápidas ───────────────────────────────────────────────────

    function renderSuggestions() {
        SUGGESTIONS.forEach(text => {
            const btn = document.createElement("button");
            btn.className    = "suggestion-btn";
            btn.textContent  = text;
            btn.title        = text;
            btn.addEventListener("click", () => {
                sendMessage(text);
                // Ocultar sugerencias después del primer uso
                if (suggestBox) suggestBox.style.display = "none";
            });
            suggestBox.appendChild(btn);
        });
    }

    // ─── Enviar mensaje ────────────────────────────────────────────────────────

    async function sendMessage(overrideText) {
        const text = (overrideText ?? input.value).trim();

        if (!text || isLoading) return;
        if (text.length > MAX_MSG_LEN) {
            showError(`El mensaje es demasiado largo (máx. ${MAX_MSG_LEN} caracteres).`);
            return;
        }

        // Mostrar mensaje del usuario
        addMessage("user", sanitize(text));
        input.value = "";
        autoResizeTextarea();

        // Deshabilitar input mientras carga
        setLoading(true);

        // Mostrar indicador "Escribiendo…"
        const typingEl = showTypingIndicator();

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text }),
                signal: AbortSignal.timeout(25000),   // 25 s timeout
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail ?? `Error ${response.status}`);
            }

            const data = await response.json();
            removeTypingIndicator(typingEl);
            addMessage("bot", data.response ?? "No se recibió respuesta.");

        } catch (err) {
            removeTypingIndicator(typingEl);

            if (err.name === "TimeoutError") {
                showError("La respuesta tardó demasiado. Intenta de nuevo.");
            } else if (err.message.includes("Failed to fetch") ||
                       err.message.includes("NetworkError")) {
                showError(
                    "No se pudo conectar al servidor. " +
                    "Asegúrate de que el backend esté corriendo en http://127.0.0.1:8000"
                );
            } else {
                showError(`Error: ${err.message}`);
            }
        } finally {
            setLoading(false);
        }
    }

    // ─── Helpers de UI ────────────────────────────────────────────────────────

    /**
     * Agrega un mensaje al área de chat.
     * @param {"bot"|"user"} role
     * @param {string} text
     */
    function addMessage(role, text) {
        const el = document.createElement("div");
        el.className = `message ${role}`;

        // Convertir saltos de línea en <br> y respetar listas simples
        el.innerHTML = formatMessageText(sanitize(text));

        messages.appendChild(el);
        scrollToBottom();
        return el;
    }

    /** Muestra un mensaje de error estilizado */
    function showError(msg) {
        const el = document.createElement("div");
        el.className = "message bot";
        el.style.borderColor = "rgba(255, 80, 80, 0.3)";
        el.style.background  = "rgba(255, 80, 80, 0.08)";
        el.style.color       = "#fca5a5";
        el.textContent       = "⚠️ " + msg;
        messages.appendChild(el);
        scrollToBottom();
    }

    /** Muestra el indicador de escritura y retorna el elemento */
    function showTypingIndicator() {
        const el = document.createElement("div");
        el.className = "typing-indicator";
        el.innerHTML = "<span></span><span></span><span></span>";
        messages.appendChild(el);
        scrollToBottom();
        return el;
    }

    /** Elimina el indicador de escritura */
    function removeTypingIndicator(el) {
        if (el && el.parentNode) el.parentNode.removeChild(el);
    }

    /** Habilita / deshabilita el estado de carga */
    function setLoading(state) {
        isLoading       = state;
        sendBtn.disabled = state;
        input.disabled   = state;
        if (!state) input.focus();
    }

    /** Scroll suave al último mensaje */
    function scrollToBottom() {
        requestAnimationFrame(() => {
            messages.scrollTop = messages.scrollHeight;
        });
    }

    // ─── Formateo de texto ─────────────────────────────────────────────────────

    /**
     * Sanitiza texto para evitar XSS.
     * Convierte caracteres especiales HTML.
     */
    function sanitize(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Convierte texto plano en HTML básico:
     * - \n → <br>
     * - Líneas que comienzan con "- " → lista visual
     */
    function formatMessageText(html) {
        return html
            .replace(/\n- /g, "\n• ")     // Normalizar listas
            .replace(/\n/g, "<br>");
    }

    // ─── Textarea auto-resize ──────────────────────────────────────────────────

    function autoResizeTextarea() {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 100) + "px";
    }

    input.addEventListener("input", autoResizeTextarea);

    // ─── Enviar con Enter (Shift+Enter = nueva línea) ──────────────────────────

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener("click", () => sendMessage());

    // ─── Accesibilidad: cerrar con Escape ─────────────────────────────────────

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && isOpen) {
            isOpen = false;
            toggle.classList.remove("open");
            window_.classList.remove("open");
        }
    });

})();
