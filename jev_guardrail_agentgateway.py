"""Levanta agentgateway standalone (1.7.0) con System One: JEV en la nube,
modelos locales (Laya, Julia-1) y un guardrail delante de un modelo real de
OpenRouter.

Requiere, en terminales aparte:
  1. python jev_guardrail_webhook.py   (el gate en localhost:8000)
  2. python jev_guardrail_agentgateway.py   (este script, agentgateway en localhost:4000)

La config (agentgateway.config.template.yaml) define estos modelos:
  - "openrouter": el modelo protegido (openai/gpt-oss-20b, de pago pero muy
    barato; los slugs ":free" comparten pool y devuelven 429 con facilidad).
    Cualquier POST a http://localhost:4000/v1/chat/completions con este modelo
    pasa primero por el webhook de JEV (jev_guardrail_webhook.py); si el score
    de jailbreak/harmful/secrets llega al umbral, agentgateway devuelve 403
    sin que la peticion toque el modelo.
  - "jev": JEV por la API nativa de TypeSafe, con el proveedor "typesafe" de la
    1.7.0. El webhook llama a JEV A TRAVES de este modelo, asi el coste y la
    latencia de la propia evaluacion tambien quedan registrados por el gateway.
  - "laya", "laya-ml" y "julia": servidores locales que hablan /v1/systemone,
    declarados como proveedor custom con el formato systemOne.

agentgateway no soporta variables de entorno en su YAML (solo valor
inline o {file: ruta}), asi que este script sustituye 3 placeholders sobre
una copia temporal del template antes de arrancar el binario:
  __OPENROUTER_API_KEY__  -> la key de OpenRouter, para no commitearla en claro.
  __TYPESAFE_API_KEY__    -> la key de TypeSafe (JEV).
  __DB_PATH__             -> <repo>/request-logs.db, un fichero SQLite donde
                              agentgateway guarda el log de peticion. Sin
                              esto, las pestanas Logs/Analytics de la UI
                              (localhost:15000/ui) y `agctl standalone
                              analytics` no tienen datos.
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
    if not KEY:
        # Sin key de OpenRouter solo falla el modelo protegido del chat.
        print("AVISO: falta OPENROUTER_API_KEY en .env; el chat protegido no funcionara.")
    if not TS_KEY:
        print("AVISO: falta TYPESAFE_API_KEY en .env; JEV no funcionara (los locales si).")

    with open(TEMPLATE) as f:
        rendered = f.read()
    rendered = rendered.replace("__OPENROUTER_API_KEY__", KEY or "sin-key")
    rendered = rendered.replace("__TYPESAFE_API_KEY__", TS_KEY or "sin-key")
    rendered = rendered.replace("__DB_PATH__", DB_PATH)

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(rendered)
        config_path = f.name

    print(f"Config renderizada (temporal, con las keys reales): {config_path}")
    print("Lanzando agentgateway en :4000, guardrail JEV en :8000 (Ctrl+C para parar)\n")
    try:
        subprocess.run([agentgateway_bin(), "-f", config_path])
    finally:
        os.unlink(config_path)


if __name__ == "__main__":
    main()
