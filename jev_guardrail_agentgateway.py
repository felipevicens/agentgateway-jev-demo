"""Levanta agentgateway standalone con el guardrail JEV delante de un
modelo real de OpenRouter.

Requiere, en 2 terminales aparte:
  1. python jev_guardrail_webhook.py   (el gate en localhost:8000)
  2. python jev_guardrail_agentgateway.py   (este script, agentgateway en localhost:4000)

La config define 2 modelos en agentgateway:
  - "openrouter": el modelo protegido (openai/gpt-oss-20b, de pago pero muy
    barato, ~$0.018/millon de tokens; los slugs ":free" comparten pool y
    devuelven 429 con facilidad). Cualquier POST a
    http://localhost:4000/v1/chat/completions con este modelo pasa primero
    por el webhook de JEV (jev_guardrail_webhook.py); si el score de
    jailbreak/harmful/secrets llega al umbral, agentgateway devuelve 403
    sin que la peticion toque el modelo.
  - "jev": el propio JEV (typesafe/jev-1.13 via OpenRouter, endpoint nativo
    /api/alpha/decisions, con passthrough: detect). El webhook llama a JEV
    A TRAVES de este modelo en vez de directo a OpenRouter, asi el coste y
    la latencia de la propia evaluacion tambien quedan registrados por el
    gateway. Mismo patron que el ejemplo oficial
    agentgateway/examples/llm-guardrail-jev.

agentgateway no soporta variables de entorno en su YAML (solo valor
inline o {file: ruta}), asi que este script sustituye 2 placeholders sobre
una copia temporal del template antes de arrancar el binario:
  __OPENROUTER_API_KEY__  -> la key real, para no commitearla en claro.
  __DB_PATH__             -> <repo>/request-logs.db, un fichero SQLite donde
                              agentgateway guarda el log de peticion. Sin
                              esto, las pestanas Logs/Analytics de la UI
                              (localhost:15000/ui) dan "request log database
                              is not configured".

"""

import os
import subprocess
import tempfile

from dotenv import load_dotenv

load_dotenv()
KEY = os.environ.get("OPENROUTER_API_KEY", "")
TS_KEY = os.environ.get("TYPESAFE_API_KEY", "")

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "agentgateway.config.template.yaml")
# Fichero SQLite donde agentgateway guarda el log de peticion, para que las
# pestanas Logs/Analytics de la UI (localhost:15000/ui) tengan datos. Ruta
# absoluta bajo el repo, asi no depende del directorio de donde se lance.
DB_PATH = os.path.join(HERE, "request-logs.db")


def agentgateway_bin():
    """Binario de agentgateway: AGENTGATEWAY_BIN, ./bin/ (scripts/instalar.sh),
    ~/.local/bin o el PATH, por este orden."""
    candidatos = [os.environ.get("AGENTGATEWAY_BIN"),
                  os.path.join(HERE, "bin", "agentgateway"),
                  os.path.expanduser("~/.local/bin/agentgateway")]
    return next((c for c in candidatos if c and os.path.exists(c)), "agentgateway")


def main():
    key = KEY
    if not key:
        # Sin key solo funciona el backend local (laya) y la ruta de rechazo
        # del guardrail; el modelo protegido y JEV via OpenRouter fallaran.
        print("AVISO: falta OPENROUTER_API_KEY en .env; solo funcionara Laya.")
        key = "sin-key"

    with open(TEMPLATE) as f:
        rendered = f.read()
    rendered = rendered.replace("__OPENROUTER_API_KEY__", key)
    rendered = rendered.replace("__TYPESAFE_API_KEY__", TS_KEY or "sin-key")
    rendered = rendered.replace("__CATALOG_FILE__", os.path.join(HERE, "catalog", "model-catalog.compat.json"))
    rendered = rendered.replace("__DB_PATH__", DB_PATH)

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(rendered)
        config_path = f.name

    print(f"Config renderizada (temporal, con la key real): {config_path}")
    print("Lanzando agentgateway en :4000, guardrail JEV en :8000 (Ctrl+C para parar)\n")
    try:
        subprocess.run([agentgateway_bin(), "-f", config_path])
    finally:
        os.unlink(config_path)


if __name__ == "__main__":
    main()
