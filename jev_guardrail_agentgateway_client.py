"""Manda los mismos 5 mensajes de prueba de jev_guardrail.py, pero contra
el agentgateway standalone real (jev_guardrail_agentgateway.py) en vez de
llamar a JEV directamente.

Requiere que ya esten corriendo, en terminales aparte:
  python jev_guardrail_webhook.py
  python jev_guardrail_agentgateway.py
"""

import time

import requests

from jev_guardrail import MESSAGES

GATEWAY = "http://localhost:4000/v1/chat/completions"


def main():
    for i, (label, msg) in enumerate(MESSAGES, 1):
        t0 = time.perf_counter()
        r = requests.post(
            GATEWAY,
            json={"model": "openrouter", "messages": [{"role": "user", "content": msg}]},
            timeout=60,
        )
        lat_ms = (time.perf_counter() - t0) * 1000

        print(f"\n=== {i}/{len(MESSAGES)} [{label}] ===")
        print(f"  msg : «{msg[:78]}{'…' if len(msg) > 78 else ''}»")
        print(f"  HTTP: {r.status_code}  ({lat_ms:.0f} ms)")
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            print(f"  respuesta del modelo: «{content[:150]}»")
        else:
            print(f"  bloqueado por el guardrail: {r.text}")


if __name__ == "__main__":
    main()
