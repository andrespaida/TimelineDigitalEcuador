"""
utils/html_parser.py — Parser inteligente del HTML de la línea de tiempo
Extrae, limpia y divide el contenido en chunks relevantes.
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup


# ─── Constantes ───────────────────────────────────────────────────────────────

MAX_CHUNK_CHARS = 800     # Máximo de caracteres por chunk
MIN_RELEVANCE_SCORE = 1   # Mínimo de términos coincidentes para incluir chunk


class HTMLParser:
    """
    Parsea el HTML de la línea de tiempo y expone métodos para
    recuperar fragmentos relevantes según una consulta.
    """

    def __init__(self, html_path: str) -> None:
        self.html_path = html_path
        self._chunks: List[Dict[str, str]] = []
        self._load_and_parse()

    # ─── Carga y parseo inicial ────────────────────────────────────────────────

    def _load_and_parse(self) -> None:
        """Lee el HTML y construye los chunks una sola vez al arrancar."""
        try:
            with open(self.html_path, "r", encoding="utf-8") as f:
                raw_html = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"No se encontró el archivo HTML en: {self.html_path}"
            )

        soup = BeautifulSoup(raw_html, "html.parser")

        # Eliminar scripts y estilos para quedarnos solo con contenido visible
        for tag in soup(["script", "style", "meta", "link", "head"]):
            tag.decompose()

        self._chunks = self._extract_timeline_chunks(soup)

    def _extract_timeline_chunks(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extrae cada nodo de la línea de tiempo como un chunk independiente.
        Cada chunk contiene: año, título de ley, descripción y beneficio.
        """
        chunks: List[Dict[str, str]] = []

        # Cada evento de la línea de tiempo está en .timeline-item
        items = soup.select(".timeline-item")

        for item in items:
            year_el   = item.select_one(".year-circle")
            title_el  = item.select_one("h4")
            desc_el   = item.select_one(".description")
            help_el   = item.select_one(".help-box")

            year  = year_el.get_text(strip=True)  if year_el  else "Año desconocido"
            title = title_el.get_text(strip=True) if title_el else "Sin título"
            desc  = desc_el.get_text(strip=True)  if desc_el  else ""
            help  = help_el.get_text(strip=True)  if help_el  else ""

            # Texto limpio del chunk
            text = (
                f"[{year}] {title}\n"
                f"Descripción: {desc}\n"
                f"Beneficio: {help}"
            )

            chunks.append({
                "year":  year,
                "title": title,
                "text":  text,
            })

        # Fallback: si no hay .timeline-item, extraer todo el texto visible
        if not chunks:
            full_text = soup.get_text(separator="\n", strip=True)
            clean     = self._clean_text(full_text)
            chunks    = [{"year": "general", "title": "Contenido completo", "text": clean}]

        return chunks

    # ─── Limpieza de texto ────────────────────────────────────────────────────

    @staticmethod
    def _clean_text(text: str) -> str:
        """Elimina espacios múltiples y líneas vacías del texto."""
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    # ─── Búsqueda por relevancia ──────────────────────────────────────────────

    def _relevance_score(self, chunk: Dict[str, str], query: str) -> int:
        """
        Calcula un score de relevancia simple basado en coincidencia de términos.
        Retorna el número de términos del query que aparecen en el chunk.
        """
        # Tokens del query: palabras de más de 3 letras (ignorar stopwords simples)
        stopwords = {
            "que", "para", "con", "los", "las", "del", "una", "como",
            "más", "por", "este", "esta", "son", "fue", "hay", "sobre",
        }
        query_tokens = [
            t.lower() for t in re.split(r"\W+", query)
            if len(t) > 3 and t.lower() not in stopwords
        ]

        chunk_text_lower = chunk["text"].lower()
        score = sum(1 for token in query_tokens if token in chunk_text_lower)
        return score

    # ─── API pública ──────────────────────────────────────────────────────────

    def get_relevant_chunks(self, query: str, top_k: int = 7) -> List[str]:
        """
        Devuelve chunks relevantes. Para preguntas generales envía todos.
        """
        # Palabras clave que indican pregunta general → enviar TODO el contexto
        general_keywords = [
            "preparado", "gobierno electronico", "gobierno electrónico",
            "resumen", "todas", "cuántas", "cuantas", "leyes", "evolución",
            "evolucion", "historia", "general", "ecuador digital", "todo"
        ]

        query_lower = query.lower()
        is_general = any(kw in query_lower for kw in general_keywords)

        if is_general:
            # Enviar todos los chunks para preguntas globales
            return [chunk["text"] for chunk in self._chunks]

        # Para preguntas específicas, usar scoring de relevancia
        scored = [
            (chunk, self._relevance_score(chunk, query))
            for chunk in self._chunks
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        relevant = [c for c, s in scored if s >= MIN_RELEVANCE_SCORE]

        if not relevant:
            relevant = self._chunks

        result = []
        for chunk in relevant[:top_k]:
            text = chunk["text"]
            if len(text) > MAX_CHUNK_CHARS:
                text = text[:MAX_CHUNK_CHARS] + "..."
            result.append(text)

        return result

    def get_all_chunks(self) -> List[Dict[str, str]]:
        """Devuelve todos los chunks (para el endpoint de debug)."""
        return self._chunks
