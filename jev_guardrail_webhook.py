"""Webhook real de guardrail para agentgateway standalone.

Implementa el contrato `promptGuard.request[].webhook` de agentgateway
(fuente verificada en agentgateway/agentgateway,
crates/agentgateway/src/llm/policy/webhook.rs): agentgateway hace
POST /request con {"body": {"messages": [...]}} y espera de vuelta
{"action": {...}}, donde un objeto vacio es Pass y {"body": str,
"status_code": int} es Reject. No hay clave "reject"/"pass" anidada, el
objeto action completo ES la accion.

Reutiliza los mismos evaluadores, escala y umbral de jev_guardrail.py, asi
que el veredicto usa las mismas preguntas y el mismo criterio que el script
standalone. A diferencia de jev_guardrail.py (que llama a OpenRouter
directo con requests), este webhook llama a JEV A TRAVES del propio
agentgateway (modelo "jev" en agentgateway.config.template.yaml, con
passthrough: detect), igual que hace el ejemplo oficial
agentgateway/examples/llm-guardrail-jev: asi el coste/latencia de la
propia evaluacion del guard tambien queda registrado por el gateway, no
solo el del modelo protegido.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from jev_guardrail import QUESTIONS, THRESHOLD

HOST, PORT = "localhost", 8000
GATEWAY = "http://localhost:4000"
# Backend del juez: "jev" (de pago, via OpenRouter) o "laya" (local, laya-serve).
# Se elige con GUARD_BACKEND=laya; ambos pasan por agentgateway.
BACKEND = os.environ.get("GUARD_BACKEND", "jev")


def jev_via_gateway(state, questions):
    """Pregunta al juez (JEV, Laya o Julia-1) a traves de agentgateway.

    Usa la ruta /v1/systemone, que agentgateway >= 1.6.0 detecta sola, asi que
    el coste y la latencia del propio juez tambien quedan registrados.
    """
    # Ruta /v1/systemone detectada por agentgateway >= 1.6.0, sin "messages".
    url = f"{GATEWAY}/v1/systemone"
    body = {"model": BACKEND, "state": state, "questions": questions}
    t0 = time.perf_counter()
    r = requests.post(url, json=body, timeout=60)
    lat_ms = (time.perf_counter() - t0) * 1000
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
    return r.json(), lat_ms


class GuardrailHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/request":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        incoming = json.loads(self.rfile.read(length) or b"{}")
        messages = incoming.get("body", {}).get("messages", [])

        try:
            data, lat_ms = jev_via_gateway({"messages": messages}, QUESTIONS)
        except Exception as e:  # falla del propio JEV -> deja pasar y avisa
            print(f"[webhook] ERROR llamando a JEV: {e}")
            self._respond({"action": {}})
            return

        rejected = []
        for name in ("jailbreak", "harmful", "secrets"):
            a = data["answers"][name]
            if a["score"] >= THRESHOLD:
                rejected.append(f"{name}={a['score']:.2f}")

        if rejected:
            reason = ", ".join(rejected)
            action = {
                "body": f"Rejected by {BACKEND}: {reason}",
                "status_code": 403,
                "reason": reason,
            }
            print(f"[webhook] BLOCK ({lat_ms:.0f} ms) {reason}")
        else:
            action = {}
            print(f"[webhook] PASS  ({lat_ms:.0f} ms)")

        self._respond({"action": action})

    def _respond(self, body):
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print(f"Guardrail webhook ({BACKEND}) escuchando en http://{HOST}:{PORT}/request")
    HTTPServer((HOST, PORT), GuardrailHandler).serve_forever()
