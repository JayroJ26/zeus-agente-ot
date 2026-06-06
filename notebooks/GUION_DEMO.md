# 🎬 Guion de la demo en vivo — Zeus ⚡ (5–7 min)

**Proyecto:** Zeus, agente de mantenimiento industrial · **Variante 3: generador de órdenes de trabajo (OT)**
**Autor:** Jayro Joel Rojas Avelar · Maestría en Automatización Industrial · UTH 2026.4
**Repo:** https://github.com/JayroJ26/zeus-agente-ot

> **Idea de una frase:** un operador reporta una falla en lenguaje natural por Telegram → Zeus razona, la clasifica, la enriquece con los manuales (RAG) y devuelve una **orden de trabajo profesional en PDF**, que además **envía por correo** al responsable. El **cerebro** es la sesión de Claude Code; el código Python son las **herramientas** deterministas.

---

## ✅ Checklist ANTES de empezar (montar 10 min antes)

Abrí una terminal en la carpeta del proyecto (`zeus-agente-ot`) para cada cosa:

1. **Encender el bot de Telegram** (dejarlo corriendo, NO cerrar la terminal):
   ```powershell
   .venv\Scripts\python -X utf8 -u src\telegram_bot.py
   ```
   Debe imprimir: `Zeus escuchando en Telegram...  [ABIERTO a todos]`.

2. **Sesión de Claude Code abierta** en el repo = el **cerebro** que razona el reporte. Tené listo el **modo autónomo** (Monitor que detecta reportes nuevos en la bandeja) o, más controlado, vos le decís a Claude "procesá el reporte nuevo" cuando llegue.

3. **Telegram a la vista**: el chat con **@TeslaProm_bot** abierto en el celular o en Telegram Web, proyectado.

4. **Gmail abierto** en `jayrojoel1009@gmail.com` para mostrar el correo que llega (asunto `[Industria Alimenticia…] OT-2026-0009 - ABIERTA`).

5. **JupyterLab abierto** con el notebook de respaldo **ya ejecutado** (plan B):
   ```powershell
   .venv\Scripts\jupyter lab
   ```
   → abrir `notebooks/demo.ipynb` (ya tiene todas las salidas incrustadas; aunque falle el internet, se ve completo).

6. **Datos por si los piden:** contador de folios en **8** → esta demo emite **OT-2026-0009**. Hay 2 manuales en el RAG (**295 fragmentos**: WEG + ANSI/NETA).

> 💡 **Tip de oro:** practicá el flujo una vez completo antes de presentar. Y si querés que la demo en vivo **no gaste folio real ni dependa del internet**, apoyate en el notebook con `MODO_ENSAYO = True` y `ENVIAR_CORREO = True` (manda el correo de verdad pero el folio va a un contador temporal).

---

## 🗺️ Mapa: qué requisito de la rúbrica cae en cada momento

| Momento | Acción | Requisito |
|---|---|---|
| Intro + arquitectura | POO (herencia/polimorfismo) + system prompt | (1), (5) |
| Reporte por Telegram → OT | Tool calling + canal de salida | (3), (4) |
| Acciones del PDF | RAG sobre 2 manuales | (2) |
| Correo con la OT | Segundo canal de salida | (4) |
| Datos faltantes + `/pruebas` + "terminada" | Ciclo de vida ABIERTA→FINALIZADA | — |
| Repo + `.env` | GitHub público + secrets fuera del código | (7), (8) |

---

## ⏱️ Guion minuto a minuto

### [0:00 – 0:40] · Presentación
> «Soy Jayro. Mi proyecto es **Zeus**, un agente de mantenimiento industrial. La variante que me tocó es la **3: generar órdenes de trabajo**. La idea: el operador de planta describe la falla con sus palabras por **Telegram**, y Zeus le devuelve una **orden de trabajo profesional en PDF**, fundamentada en los manuales del equipo, y se la **manda también por correo** al responsable. El cerebro que razona es la sesión de **Claude Code**; el código Python son las herramientas que ejecuta.»

### [0:40 – 1:40] · Arquitectura y POO *(req 1 y 5)*
- Mostrá `src/modelos.py` unos segundos:
  > «Todo es **orientado a objetos**: una clase base `OrdenDeTrabajo` y, por **herencia**, una subclase por tipo de equipo — `OrdenTrabajoMotor`, `OrdenTrabajoGenerador`, `OrdenTrabajoTransformador`. Cada una, por **polimorfismo**, define su propio checklist de pruebas y sus campos obligatorios.»
- Mostrá `CLAUDE.md` un segundo:
  > «Este es el **system prompt** de Zeus: su identidad, cómo clasifica prioridad y tipo, y la regla de no inventar datos.»

### [1:40 – 4:00] · El flujo completo, EN VIVO por Telegram *(req 3 y 4 + ciclo de vida)*
1. **Mandá el reporte** desde Telegram (copiá-pegá):
   > *«El motor M-015 de la línea de envasado 2 está recalentando, huele a quemado y el guardamotor ya disparó dos veces hoy. Es un Siemens. Urge.»*
2. **Claude razona** (mostralo en la sesión): elige `OrdenTrabajoMotor`, prioridad **ALTA**, tipo **correctivo**; consulta el **RAG** para las acciones; crea la **OT-2026-0009** *ABIERTA*.
3. **En Telegram llegan**: el **PDF** de la OT + la **solicitud de datos faltantes** + el **aviso del checklist**. → Abrí el PDF en el cel y mostralo.
4. **En Gmail llega** el correo `[Industria Alimenticia Hondureña S.A.] Orden de trabajo OT-2026-0009 - ABIERTA`, con el **cuadro-resumen profesional** y el **PDF adjunto**. *(req 4: segundo canal)*
5. **Respondé los datos** por Telegram (un dato por línea):
   > `Tag: M-015`
   > `Modelo: 1LE1003`
   > `Clase de aislamiento: F`
   → Zeus confirma con **texto, sin PDF** (la *regla del PDF*: el PDF solo al crear, al finalizar y si lo pedís).
6. **Llená el checklist** con **`/pruebas`** (guiado, una por una). Mostrá 2–3 pruebas; incluí una **fuera de rango** (ej. `Temperatura: 96 | fuera de rango`) para que se vea el coloreado.
7. **Cerrá la OT**: escribí **`terminada`**. Zeus valida que no falten datos, marca **FINALIZADA**, regenera el **PDF final con el badge verde** y lo manda por Telegram **+ correo** `… - FINALIZADA`.

### [4:00 – 4:30] · Subrayá el RAG *(req 2)*
- Señalá en el PDF la sección **«Acciones recomendadas»**:
  > «Esto no lo inventé yo en el código: Zeus lo **recuperó de los manuales** con su RAG — ajustar el relé térmico a In×FS, vigilar la clase de aislamiento, sensores Pt-100. Son **2 manuales** (guía de motores **WEG** y el estándar **ANSI/NETA**), **295 fragmentos**, búsqueda por palabra clave filtrada por tipo de equipo.»

### [4:30 – 5:45] · Notebook: el pipeline pieza por pieza (y plan B) *(req 1, 2, 3, 4)*
- Abrí `notebooks/demo.ipynb` en JupyterLab:
  > «Por si la red de Telegram falla, y para ver el motor por dentro, armé este notebook que recorre **todo el pipeline en local**.»
- Recorré (o mostrá ya ejecutado): **POO** (folio único, herencia, polimorfismo) → **RAG** (los fragmentos térmicos) → **datos faltantes** → **checklist** → **PDF renderizado dentro del notebook** → **cuerpo del correo** → **finalizar**.
- Frase: «Corre las veces que quiera sin gastar folios reales, gracias al `MODO_ENSAYO`.»

### [5:45 – 6:30] · Cierre + rúbrica
> «En resumen, Zeus cumple: **(1)** POO con herencia y polimorfismo; **(2)** RAG sobre 2 PDFs; **(3)** herramientas vía tool calling; **(4)** doble salida, **Telegram y correo**; **(5)** system prompt en `CLAUDE.md`; **(7)** repo público en GitHub con README; **(8)** los secretos en `.env`, fuera del código. Y todo el flujo es **autónomo**: Zeus razona cada reporte y responde solo. Gracias.»

---

## 🛟 Plan de contingencia (si algo falla en vivo)

| Si falla… | Qué hacer |
|---|---|
| **Telegram da `TimedOut`** al enviar | **NO** recrear la OT (gastaría otro folio y la duplicaría). Recargá la OT del almacén y reintentá **solo el envío**. O saltá directo al **notebook** (no usa Telegram). |
| **No llega el correo** | Mostralo en el notebook: la celda del paso 6 renderiza el **cuerpo HTML del correo** aunque no se envíe. |
| **El bot no responde** | Verificá que la terminal del bot siga viva (un solo listener aparece como **2 procesos** `python.exe`, no es conflicto). Si murió, relanzalo (comando del checklist). |
| **Se cae todo / sin internet** | El **notebook ya ejecutado** tiene TODAS las salidas incrustadas (PDF incluido): hacé scroll y narralo. Es el plan B completo. |
| **Piden correr el notebook y no arranca el kernel** | Cerrá y reabrí el kernel, o mostrá el `.ipynb` ya ejecutado (las salidas están guardadas en el archivo). |

---

## 🧰 Chuleta de comandos

```powershell
# Encender el bot (dejar corriendo)
.venv\Scripts\python -X utf8 -u src\telegram_bot.py

# Abrir el notebook de respaldo
.venv\Scripts\jupyter lab           # luego abrir notebooks/demo.ipynb

# Ver el estado de los folios (sin gastar ninguno)
.venv\Scripts\python src\folios.py

# Ver las OT guardadas y su estado
.venv\Scripts\python src\almacen.py
```

**Para la demo del notebook**, en la celda 0 (Configuración):
- `MODO_ENSAYO = True` → no toca folios/almacén reales (ideal para ensayar y para no gastar el folio real).
- `ENVIAR_CORREO = True` → manda el correo de verdad (impacta mostrar la bandeja). Se puede combinar con `MODO_ENSAYO = True`.

---

## 🎤 Datos a la mano (por si preguntan)

- **Bot:** @TeslaProm_bot · **chat_id** de Jayro: `664366522`
- **Correo de Zeus:** jayrojoel1009@gmail.com (se envía a sí mismo; para mandar al responsable real, llenar `OT_DESTINATARIO` en `.env`)
- **Tipos de OT:** Motor, Generador eléctrico, Transformador (cada uno su checklist por polimorfismo)
- **RAG:** 295 fragmentos = 268 (guía de motores WEG) + 27 (ANSI/NETA ATS-2009)
- **Cerebro sin costo:** usa la sesión de Claude Code, sin API key
- **Secrets:** `.env` (en `.gitignore`); el código nunca los lleva escritos
