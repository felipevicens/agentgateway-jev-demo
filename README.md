# System One con agentgateway: JEV y modelos locales

Montaje paso a paso para probar un modelo **System One** (JEV, de TypeSafe) y
dos modelos locales (**Laya** y **Julia-1**) detrás de un mismo
[agentgateway](https://github.com/agentgateway/agentgateway), con una web
interactiva para verlos funcionar.

Un modelo System One no escribe texto: contesta con una decisión (un sí/no,
una opción o una puntuación) y la probabilidad de cada respuesta, todo de una
sola pasada. Aquí lo llamamos siempre por la misma ruta, `/v1/systemone`, y
solo cambia el nombre del modelo.

```
 curl / web ──► agentgateway :4000 ──┬─► jev      (API de TypeSafe, en la nube)
                  /v1/systemone      ├─► laya     (laya-serve,   :8100, local)
                                     ├─► laya-ml  (checkpoint multilingüe)
                                     └─► julia    (Julia-1,      :8200, local)
        webhook del guardrail :8000  ◄── el gateway le pregunta antes de dejar pasar un chat
```

## Índice

0. [Requisitos](#0-requisitos)
1. [Clonar y claves](#1-clonar-y-claves)
2. [Instalar agentgateway](#2-instalar-agentgateway)
3. [Instalar Laya](#3-instalar-laya)
4. [Instalar Julia-1](#4-instalar-julia-1)
5. [Arrancar todo](#5-arrancar-todo)
6. [Primeras peticiones con curl](#6-primeras-peticiones-con-curl)
7. [Benchmark de 24 casos](#7-benchmark-de-24-casos)
8. [La web interactiva](#8-la-web-interactiva)
9. [Repetir en CPU](#9-repetir-en-cpu)
10. [Costes y catálogo de precios](#10-costes-y-catálogo-de-precios)
11. [Problemas conocidos](#11-problemas-conocidos)
12. [Parar y limpiar](#12-parar-y-limpiar)
13. [Licencias y créditos](#13-licencias-y-créditos)

---

## 0. Requisitos

- Linux o WSL2 (Ubuntu), con `python3` (3.10 o superior), `git` y `curl`.
- Opcional: una GPU NVIDIA. Sin GPU todo funciona en CPU, más lento.
- Una clave de TypeSafe (`TYPESAFE_API_KEY`). La de OpenRouter solo hace falta
  para el chat protegido y para la comparativa de favoritos con un LLM.
- Espacio en disco: unos **9 GB** (PyTorch ocupa unos 6-7 GB y los modelos casi
  2 GB). Mira antes cuánto tienes libre:

```bash
df -h .
```

Si el disco justo es el de WSL, puedes llevar lo pesado a otra unidad antes de
instalar (ver [Dónde se instala cada cosa](#dónde-se-instala-cada-cosa)).

## 1. Clonar y claves

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
```

Crea el fichero `.env` a partir del ejemplo y rellena las claves. **Nunca se
sube a git y no lo enseñes en pantalla.**

```bash
cp .env.example .env
```

```bash
nano .env
```

## 2. Instalar agentgateway

Descarga el binario de la release **v1.6.0** y **verifica su SHA256**. Si no
coincide, el script aborta.

```bash
./scripts/instalar.sh gateway
```

Qué hay de especial en la v1.6.0: detecta sola la ruta `/v1/systemone`, y un
proveedor `custom` ya no necesita declarar `formats`. Por eso la plantilla
[`agentgateway.config.template.yaml`](agentgateway.config.template.yaml)
registra cada modelo con unas pocas líneas.

## 3. Instalar Laya

Crea el entorno Python (`.venv-local`), instala PyTorch, Laya y el servidor.
**Es el paso más lento** (descarga PyTorch, unos 2,5 GB). Al final comprueba
que la GPU tiene kernels.

```bash
./scripts/instalar.sh laya
```

Por defecto usa PyTorch con CUDA 12.6 (`cu126`), que también sirve para GPUs
antiguas (por ejemplo, las GTX 900). Sin GPU, instala la versión de CPU, mucho
más ligera:

```bash
TORCH_VARIANT=cpu ./scripts/instalar.sh laya
```

Los pesos de Laya se descargan solos la primera vez que arranca.

## 4. Instalar Julia-1

Descarga el modelo (safetensors y GGUF) y la versión de `transformers` que
necesita su runtime, instalada aparte para no mezclarla con la de Laya.

```bash
./scripts/instalar.sh julia
```

> Los pasos 2, 3 y 4 juntos: `./scripts/instalar.sh todo`

### Dónde se instala cada cosa

| Variable | Por defecto | Qué es |
|---|---|---|
| `VENV` | `./.venv-local` | Entorno Python |
| `BIN` | `./bin` | Binario de agentgateway |
| `MODELS` | `./models` | Julia-1 y la caché de Hugging Face (donde se baja Laya) |
| `PYLIBS` | `./pylibs/tf50` | `transformers` solo para Julia-1 |
| `TORCH_VARIANT` | `cu126` | `cpu` si no hay GPU |

Para llevarlo a otra unidad, exporta las variables **en cada terminal** antes
de instalar y de arrancar:

```bash
export VENV=/mnt/e/system-one/venv MODELS=/mnt/e/system-one/models PYLIBS=/mnt/e/system-one/pylibs
```

## 5. Arrancar todo

Abre una terminal por servidor y arráncalos **en este orden**. Cada script
libera su puerto si estaba ocupado.

**Terminal 1: Laya** (`:8100`)

```bash
./scripts/lanzar_laya.sh gpu
```

**Terminal 2: Julia-1** (`:8200`, tarda un minuto en cargar)

```bash
./scripts/lanzar_julia.sh gpu
```

**Terminal 3: webhook del guardrail** (`:8000`)

```bash
./scripts/lanzar_webhook.sh
```

**Terminal 4: agentgateway** (`:4000`)

```bash
./scripts/lanzar_gateway.sh
```

**Terminal 5: comprobar qué responde**

```bash
./scripts/estado.sh
```

Debe poner `OK` en el gateway, Laya, Julia-1 y el webhook, e indicar la GPU y
el disco.

La interfaz del gateway (con el log de cada llamada) está en
<http://localhost:15000/ui>.

## 6. Primeras peticiones con curl

Todas van al gateway, a la misma ruta; **solo cambia `"model"`**: `jev`,
`laya`, `laya-ml` o `julia`.

**`noul`: una probabilidad de sí/no**

```bash
curl -s http://localhost:4000/v1/systemone -H 'Content-Type: application/json' -d '{
  "model": "jev",
  "state": {"mensaje": "Qué bien, otro lunes lloviendo"},
  "questions": {"es_sarcasmo": {"type": "noul", "instructions": "¿Este mensaje contiene sarcasmo o ironía?"}}
}' | python3 -m json.tool
```

**`choice`: una opción entre varias, con su distribución**

```bash
curl -s http://localhost:4000/v1/systemone -H 'Content-Type: application/json' -d '{
  "model": "jev",
  "state": {"mensaje": "Menuda sorpresa, otra reunión que podría haber sido un email"},
  "questions": {"emoji": {"type": "choice", "instructions": "¿Qué emoji describe mejor la reacción a este mensaje?",
    "criteria": {"🤩": "Entusiasmo o admiración", "😊": "Alegría o amabilidad", "😐": "Neutralidad o indiferencia", "🙄": "Sarcasmo, frustración o resignación", "😡": "Enfado visible"}}}
}' | python3 -m json.tool
```

**`score`: una puntuación en una escala**

```bash
curl -s http://localhost:4000/v1/systemone -H 'Content-Type: application/json' -d '{
  "model": "jev",
  "state": {"mensaje": "Pedí una pizza y tardó dos horas en llegar, además estaba completamente fría."},
  "questions": {"estrellas": {"type": "score", "instructions": "¿Cuántas estrellas de 1 a 5 merece esta experiencia?",
    "criteria": ["1 estrella: Pésima, inaceptable", "2 estrellas: Mala con fallos graves", "3 estrellas: Regular", "4 estrellas: Buena", "5 estrellas: Excelente"]}}
}' | python3 -m json.tool
```

**Las tres a la vez, en una sola llamada.** Para cambiar de modelo, define
`MODEL` (por defecto, `jev`):

```bash
MODEL=laya ./demo_curl.sh
```

Prueba también `MODEL=julia ./demo_curl.sh` y `MODEL=jev ./demo_curl.sh`. Las
respuestas **no son iguales**: cada modelo reparte la probabilidad a su manera.

## 7. Benchmark de 24 casos

Un guardrail de chat: tres evaluadores (`jailbreak`, `harmful`, `secrets`,
puntuaciones de 0 a 3) y la regla "bloquear si cualquiera llega a 2". Se envían
24 mensajes etiquetados (12 inocentes y 12 ataques, todos en español) y se
mide el acierto y la latencia de cada modelo por el gateway.

Activa el entorno para poder ejecutar `bench.py`:

```bash
source .venv-local/bin/activate
```

```bash
python bench.py run jev:nube laya:GPU julia:GPU
```

Cada argumento es `MODELO:ETIQUETA` (la etiqueta es solo el texto de la columna
"Dispositivo"). Los resultados se acumulan en `bench-results.json`, así que
puedes añadir más después y ver la tabla completa cuando quieras:

```bash
python bench.py tabla
```

Para empezar de cero:

```bash
python bench.py reset
```

> Los modelos de nube cambian: repite la medición el mismo día en que vayas a
> enseñarla, y no te fíes de cifras de otras sesiones.

## 8. La web interactiva

Con el gateway y los modelos arrancados (paso 5):

```bash
./scripts/lanzar_web.sh
```

Ábrela en <http://localhost:3000>. Tiene cuatro bloques:

- **Primitivas:** el mismo mensaje con `noul`, `choice`, `score` y las tres
  juntas, contra el modelo que elijas.
- **Benchmark:** los 24 casos del guardrail, uno a uno, con su latencia.
- **Favoritos:** 16 enlaces ordenados en carpetas con **una sola llamada** a
  JEV, frente a un LLM generando texto (este último necesita
  `OPENROUTER_API_KEY`).
- **Chat protegido:** un chat cuyo guardrail es el webhook (necesita el
  webhook y `OPENROUTER_API_KEY`).

La web solo escucha en `127.0.0.1` a propósito: su servidor lee tus claves y no
debe exponerse a la red.

## 9. Repetir en CPU

Para medir sin GPU, reinicia los dos modelos locales en CPU y vuelve a lanzar
el benchmark con otra etiqueta:

```bash
./scripts/lanzar_laya.sh cpu
```

```bash
./scripts/lanzar_julia.sh cpu
```

```bash
python bench.py run laya:CPU julia:CPU
```

```bash
python bench.py tabla
```

Julia-1 también puede servirse con `llama.cpp` (solo CPU). Primero lo compila
(unos minutos) y luego lo arranca:

```bash
./scripts/instalar.sh llamacpp
```

```bash
./scripts/lanzar_julia.sh llamacpp
```

## 10. Costes y catálogo de precios

El gateway guarda en su base de datos (`request-logs.db`) los tokens y el coste
de cada llamada. Dos cosas a saber:

- **JEV** por la API nativa de TypeSafe devuelve tokens pero **no el coste**.
  Se calcula con el precio publicado por OpenRouter (0,042 $ por millón de
  tokens de entrada, salida sin coste), que está en
  [`scripts/catalogo_compatible.py`](scripts/catalogo_compatible.py).
  **Contrástalo con el de TypeSafe**: es el precio de otra vía.
- El catálogo de precios que descarga el botón *Refresh base costs* de la
  interfaz usa un formato que la v1.6.0 no entiende (fallo: `decode model
  catalog from GitHub`). Por eso `lanzar_gateway.sh` genera una copia
  compatible en `catalog/` y el gateway la carga solo. **No hace falta pulsar
  ese botón.**

## 11. Problemas conocidos

- **GPU antigua (por ejemplo, Maxwell):** las versiones recientes de PyTorch
  (`cu130`) no traen kernels para ella y fallan con `no kernel image is
  available`. Por eso el instalador usa `cu126`.
- **Caída silenciosa a CPU:** si Laya no puede usar la GPU, **sigue funcionando
  en CPU sin avisar**. Mira el campo `device` en
  `curl localhost:8100/health` (lo muestra `estado.sh`).
- **Dos checkpoints en Laya:** el campo `"model"` de la petición elige el
  checkpoint. `"laya"` es el **inglés** (421M); el multilingüe (322M) es
  `"multilingual"`, y en el gateway se llama `laya-ml`. La respuesta trae
  `routing.model` con el que se usó de verdad.
- **Memoria de la GPU:** Laya con los dos checkpoints y Julia-1 a la vez
  pueden rozar los 6 GB. Si falla por memoria, arranca Laya con un solo
  checkpoint: `LAYA_MODELS=english ./scripts/lanzar_laya.sh gpu`.
- **Puerto 8000:** `laya-serve` usa el 8000 por defecto y chocaría con el
  webhook. Los scripts lo mueven al 8100.
- **Julia-1 y `transformers`:** su runtime solo funciona con `transformers
  5.0.x`; por eso va en `PYLIBS` y se antepone por `PYTHONPATH` (lo hace
  `lanzar_julia.sh`).
- **La primera llamada a un modelo local tarda unos segundos** (calentamiento);
  las siguientes, mucho menos.

## 12. Parar y limpiar

Para los servidores (gateway, webhook, Laya, Julia-1 y web):

```bash
./scripts/parar.sh
```

Para borrar lo instalado (entorno, modelos, binario y catálogo):

```bash
rm -rf .venv-local bin models pylibs catalog llama.cpp
```

## 13. Licencias y créditos

- **Laya** (Convai Innovations) y **Julia-1** (Supersonic Labs) se publican con
  licencia Apache-2.0, según sus fichas.
- **JEV** es un servicio de TypeSafe, con sus propios términos.
- **agentgateway**: consulta la licencia de su repositorio.
- Los nombres y las cifras de rendimiento que cita cada autor son suyos; las
  que aparezcan aquí, medidas en tu máquina, son las tuyas.
