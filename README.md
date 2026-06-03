# ⚡ Zeus — Agente generador de órdenes de trabajo (OT)

> **Proyecto final · Maestría en Automatización Industrial · UTH 2026.4 · Programación**
> Variante **(3)**: de un reporte en lenguaje libre del operador a una **orden de trabajo (OT) estructurada y profesional**.

**Zeus** es un agente de mantenimiento industrial. Recibe el reporte de una falla por **Telegram**, lo **razona** (con Claude Code como cerebro), lo **enriquece** con el manual del equipo vía **RAG**, genera una **orden de trabajo en PDF** profesional y la **envía** al operador — siguiendo el ciclo de vida de la OT: **abierta → finalizada**.

```
Operador (Telegram)  →  Zeus razona  →  RAG (manual)  →  OT en PDF  →  responde al operador
   "motor con guardamotor disparado"        WEG          OT-2026-0007        + checklist + datos
```

---

## ✨ Características

- 🧱 **POO** — `Equipo`, `Prueba`, `OrdenDeTrabajo` (base) → `OrdenTrabajoMotor`, `OrdenTrabajoGenerador`, `OrdenTrabajoTransformador`. Herencia + polimorfismo; cada tipo de equipo declara su **checklist** y sus **campos obligatorios**.
- 📄 **OT en PDF** profesional con `fpdf2` (encabezado, secciones, checklist coloreado, firmas), generado directo desde la OT.
- 📚 **RAG** sobre el manual del equipo (guía WEG de motores): recupera fragmentos por relevancia y Zeus redacta acciones/repuestos/tiempos.
- 💬 **Bot de Telegram** — entrada (reportes) y salida (OT + mensajes); comandos `/ayuda`, `/pruebas` (llenado guiado del checklist), `/pendientes`, `/id`; allowlist de operadores.
- 🔄 **Ciclo de vida de la OT** — nace **ABIERTA**, acumula datos y resultados de pruebas, y se **FINALIZA** cuando el operador dueño dice «terminada». Persistencia en disco.
- 🧠 **Cerebro = Claude Code** — el código Python son tools deterministas; el razonamiento lo hace la sesión de Claude (sin API key de modelo).

---

## 🎓 Cómo cumple la rúbrica

| Requisito | Cómo |
|---|---|
| **≥ 1 clase POO propia** | `Equipo`, `Prueba`, `OrdenDeTrabajo` + 3 subclases por tipo de equipo (`src/modelos.py`). |
| **RAG sobre 1-2 PDFs** | `src/rag.py` sobre la *Guía de Especificación de Motores WEG*; integrado en la creación de la OT. |
| **≥ 1 herramienta (tool calling)** | El agente ejecuta tools: crear OT, generar PDF, consultar RAG, enviar por Telegram. |
| **Canal de salida** | **Telegram** (`src/telegram_bot.py`), entrada + salida verificadas en vivo. |
| **System prompt documentado** | `CLAUDE.md` (identidad, misión, criterios de prioridad, reglas). |
| **Secrets en `.env`** | Credenciales en `.env` (ignorado por git); `.env.example` de referencia. |

---

## 🗂️ Estructura

```
zeus-agente-ot/
├── CLAUDE.md              ← system prompt del agente (identidad y reglas)
├── README.md             ← este archivo
├── requirements.txt
├── .env.example          ← variables (sin valores)
├── _procesar_reporte_demo.py
├── src/
│   ├── modelos.py        ← clases POO (Equipo, Prueba, OrdenDeTrabajo → Motor/Generador/Transformador)
│   ├── folios.py         ← folio único persistente (OT-AÑO-NNNN)
│   ├── reporte.py        ← generar_pdf(ot) / generar_html(ot)
│   ├── mensajes.py       ← diálogo con el operador (solicitar datos, parsers, detectores)
│   ├── almacen.py        ← persistencia del ciclo de vida de la OT
│   ├── agente.py         ← orquestador (crear / actualizar / finalizar / RAG)
│   ├── rag.py            ← base de conocimiento (RAG ligero)
│   ├── telegram_bot.py   ← canal de Telegram
│   └── correo.py         ← lectura de reportes por IMAP
├── data/                 ← estado de ejecución (no versionado)
└── salida/               ← OT en PDF generadas (no versionado)
```

---

## 🚀 Instalación

Requisitos: **Python 3.11+**.

```bash
# 1. Entorno virtual
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. Credenciales: copia .env.example a .env y rellénalo
#    (token del bot de @BotFather, correo, etc.)
copy .env.example .env

# 3. (Opcional) Poblar el RAG con un manual en PDF
#    .venv\Scripts\python -c "import sys; sys.path.insert(0,'src'); import rag; rag.agregar_documento(r'ruta\manual.pdf', tipo_equipo='Motor')"
```

## ▶️ Uso

```bash
# Arrancar el bot de Telegram (escucha reportes)
.venv\Scripts\python src\telegram_bot.py
```

Flujo del operador en Telegram:
1. Envía el **reporte** de la falla → Zeus crea la OT y te manda el **PDF** + la solicitud de datos.
2. Completa los **datos** faltantes y registra las **pruebas** (o usa **`/pruebas`** para llenarlas paso a paso).
3. Escribe **«terminada»** → Zeus finaliza la OT y te envía el **PDF final**.

---

## 👤 Autor

**Jayro Joel Rojas Avelar** — [@JayroJ26](https://github.com/JayroJ26)
Maestría en Automatización Industrial · UTH 2026.4
