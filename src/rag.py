"""
rag.py · Base de conocimiento (RAG ligero) de Zeus.

Guarda fragmentos de manuales / procedimientos en data/rag.json y los recupera
por relevancia (coincidencia de palabras, sin acentos). NO usa embeddings ni
APIs: Zeus (la sesión de Claude) es el cerebro que SINTETIZA; el RAG solo APORTA
los fragmentos pertinentes para que Zeus redacte acciones, repuestos y tiempos.

Para documentos en inglés conviene guardar el texto ya en ESPAÑOL (Zeus lo
traduce al ingerirlo), así la búsqueda en español encuentra los fragmentos.

  agregar(texto, fuente, tipo_equipo="", tema="")  -> añade un fragmento (id).
  buscar(consulta, k=4, tipo_equipo=None)          -> top-k fragmentos relevantes.
  agregar_documento(ruta, fuente, tipo_equipo="")  -> extrae (PDF/txt), trocea y añade.
  contar() / listar() / fuentes()                  -> inspección.
"""

import json
import os
import re
import unicodedata

_ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "rag.json",
)

# Palabras vacías (no aportan a la búsqueda).
_VACIAS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o",
           "a", "en", "con", "por", "para", "que", "se", "su", "sus", "al", "es", "son",
           "como", "mas", "este", "esta", "estos", "estas", "lo", "le", "ya", "si", "no"}


def _palabras(texto):
    """minúsculas y sin acentos -> lista de palabras (solo letras/números)."""
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", t)


def _terminos(texto):
    """Conjunto de términos significativos (palabras > 2 letras, sin vacías)."""
    return {p for p in _palabras(texto) if len(p) > 2 and p not in _VACIAS}


def _cargar():
    if not os.path.exists(_ARCHIVO):
        return []
    try:
        with open(_ARCHIVO, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _guardar(frags):
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(frags, f, ensure_ascii=False, indent=2)


def agregar(texto, fuente, tipo_equipo="", tema=""):
    """Añade un fragmento de conocimiento. Devuelve su id."""
    frags = _cargar()
    frag = {
        "id": (frags[-1]["id"] + 1) if frags else 1,
        "fuente": fuente,
        "tipo_equipo": tipo_equipo,   # "Motor" | "Generador eléctrico" | "Transformador" | ""
        "tema": tema,
        "texto": texto.strip(),
    }
    frags.append(frag)
    _guardar(frags)
    return frag["id"]


def buscar(consulta, k=4, tipo_equipo=None):
    """Devuelve los k fragmentos más relevantes a la consulta (cada uno con su
    'puntaje' = nº de términos en común). Filtra por tipo_equipo si se indica."""
    q = _terminos(consulta)
    if not q:
        return []
    resultados = []
    for frag in _cargar():
        if tipo_equipo and frag.get("tipo_equipo") and frag["tipo_equipo"] != tipo_equipo:
            continue
        palabras = _terminos(f"{frag['texto']} {frag.get('tema', '')}")
        comunes = q & palabras
        if comunes:
            resultados.append({**frag, "puntaje": len(comunes)})
    resultados.sort(key=lambda f: f["puntaje"], reverse=True)
    return resultados[:k]


def contexto(consulta, tipo_equipo="", k=5):
    """Fragmentos relevantes YA FORMATEADOS como texto (con su fuente), listos
    para que Zeus los lea y sintetice. Cadena vacía si no hay nada relevante."""
    frags = buscar(consulta, k=k, tipo_equipo=tipo_equipo or None)
    return "\n\n".join(f"[{f['fuente']}] {' '.join(f['texto'].split())}" for f in frags)


def agregar_documento(ruta, fuente="", tipo_equipo="", palabras_por_trozo=120):
    """Extrae el texto de un PDF o .txt, lo trocea y añade cada trozo. Devuelve
    cuántos fragmentos se añadieron. (Para manuales en el MISMO idioma de las
    consultas; uno en inglés conviene ingerirlo traducido con agregar().)"""
    fuente = fuente or os.path.basename(ruta)
    if ruta.lower().endswith(".pdf"):
        from pypdf import PdfReader
        texto = "\n".join((p.extract_text() or "") for p in PdfReader(ruta).pages)
    else:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            texto = f.read()
    palabras = texto.split()
    n = 0
    for i in range(0, len(palabras), palabras_por_trozo):
        trozo = " ".join(palabras[i:i + palabras_por_trozo]).strip()
        if trozo:
            agregar(trozo, fuente=fuente, tipo_equipo=tipo_equipo)
            n += 1
    return n


def contar():
    return len(_cargar())


def listar():
    return _cargar()


def fuentes():
    """Resumen {fuente: nº de fragmentos}."""
    resumen = {}
    for f in _cargar():
        resumen[f["fuente"]] = resumen.get(f["fuente"], 0) + 1
    return resumen


# === CONSULTA RÁPIDA: muestra qué hay en el RAG =============================
if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(f"Fragmentos en el RAG: {contar()}")
    for fuente, n in fuentes().items():
        print(f"  {fuente}: {n} fragmento(s)")
