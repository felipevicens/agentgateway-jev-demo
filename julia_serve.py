"""Servidor minimo /v1/systemone para Julia-1 con su runtime Python, para
poder usarlo en GPU detras del gateway.

Por que existe: llama-server (llama.cpp) ya sirve Julia-1 en /v1/systemone,
pero en esta maquina solo hay build de CPU (no hay nvcc ni toolkit CUDA). El
runtime oficial de Supersonic (`julia`) si corre en CUDA con PyTorch.

Mismo puerto que llama-server (8200): se arranca UNO de los dos, segun quieras
medir GPU o CPU, y el gateway no cambia (modelo "julia", baseUrl :8200).

  # GPU
  JULIA_DEVICE=cuda python julia_serve.py
  # CPU (alternativa a llama-server)
  JULIA_DEVICE=cpu  python julia_serve.py

Variables: JULIA_DIR (modelo, por defecto ./models/Julia-1), JULIA_DEVICE
(cuda|cpu), JULIA_HOST (127.0.0.1), JULIA_PORT (8200).

Requisito: el runtime de Julia parchea un metodo interno de transformers que
solo existe en la serie 5.0.x, asi que hay que anteponer esa version por
PYTHONPATH (ver CLAUDE.md), p. ej.:
  PYTHONPATH=./pylibs/tf50 python julia_serve.py
"""

import os
import sys
import threading

import uvicorn
from fastapi import FastAPI, HTTPException

JULIA_DIR = os.environ.get("JULIA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "Julia-1"))
DEVICE = os.environ.get("JULIA_DEVICE", "cuda")
HOST = os.environ.get("JULIA_HOST", "127.0.0.1")
PORT = int(os.environ.get("JULIA_PORT", "8200"))

# El runtime es un paquete suelto dentro del directorio del modelo.
sys.path.insert(0, JULIA_DIR)
from julia import load_model  # noqa: E402

app = FastAPI(title="Julia-1 /v1/systemone")
engine = load_model(JULIA_DIR, device=DEVICE, strict_encoding=True, max_length=8192)
lock = threading.Lock()  # un forward a la vez; la GPU/CPU ya paraleliza dentro

# El runtime no devuelve "usage". Se cuentan los tokens reales que procesa: el
# motor codifica una fila por pregunta (estado + pregunta + opciones), asi que
# el estado se cuenta una vez por pregunta, igual que lo procesa el modelo.
# Se engancha en `_encode` (interno del runtime); si cambiase, el servidor
# sigue funcionando y simplemente omite "usage".
_tokens = {"n": 0}
_encode_original = getattr(engine, "_encode", None)
if _encode_original is not None:
    def _encode_contando(rows):
        codificado = _encode_original(rows)
        try:
            _tokens["n"] += sum(len(e["ids"]) for e in codificado)
        except Exception:
            _tokens["n"] = -1
        return codificado
    engine._encode = _encode_contando


@app.get("/health")
def health():
    return {"status": "ok", "model": "julia-1", "device": DEVICE}


@app.post("/v1/systemone")
def systemone(body: dict):
    if "state" not in body or not isinstance(body.get("questions"), dict):
        raise HTTPException(422, "hacen falta 'state' y 'questions'")
    try:
        with lock:
            _tokens["n"] = 0
            res = engine.predict(state=body["state"], questions=body["questions"])
            entrada = _tokens["n"]
    except Exception as e:  # entrada invalida para el runtime -> 422
        raise HTTPException(422, str(e))
    out = {"model": "julia-1", "answers": res["answers"]}
    if entrada > 0:
        # Es un modelo que no genera texto: 0 tokens de salida (como Laya).
        out["usage"] = {"input_tokens": entrada, "output_tokens": 0}
    return out


if __name__ == "__main__":
    print(f"Julia-1 en {DEVICE}, escuchando en http://{HOST}:{PORT}/v1/systemone")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
