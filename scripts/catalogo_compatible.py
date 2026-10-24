#!/usr/bin/env python3
"""Genera un catálogo de precios de modelos que agentgateway 1.6.0 pueda leer.

El catálogo de `main` (https://agentgateway.dev/model-catalog) ya trae campos
y tramos de precio que la 1.6.0 no entiende (su decodificador es estricto) y
falla con "missing field `contextOver`". Este script:

  1. descarga el catálogo actual y el de la etiqueta de la versión instalada;
  2. de éste último aprende qué campos conoce la versión;
  3. copia el actual quitando lo desconocido: campos nuevos (capabilities,
     limits, modalities...) y los tramos de otro tipo (con `serviceTier`: precios "priority", "flex"...).

Se conservan los precios base y por tramos de contexto de TODOS los modelos,
también los publicados después de la 1.6.0. Se pierden los precios por `serviceTier`.

  python scripts/catalogo_compatible.py            # escribe catalog/model-catalog.compat.json
  python scripts/catalogo_compatible.py --salida RUTA --version v1.6.0

El gateway lo carga como fuente adicional (config.modelCatalog). Si el fichero
no existe o no es válido, usa su catálogo incorporado y no se rompe nada.
"""

import argparse
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Modelos System One que no estan en el catalogo publico. El gateway calcula el
# coste buscando proveedor + modelo tal como los registra en su log: los
# proveedores "custom" del template aparecen como proveedor "custom".
# Precios en dolares por millon de tokens (misma unidad que el catalogo).
#  - jev-latest: 0,042 $/M de entrada segun la documentacion de OpenRouter
#    (https://openrouter.ai/blog/insights/what-is-jev/); la salida no se cobra. Es el precio
#    publicado en OpenRouter: contrastarlo con el de la API nativa de TypeSafe,
#    cuya respuesta no incluye coste.
#  - modelos locales (laya, multilingual, julia): 0 (no hay coste de API).
PRECIOS_PROPIOS = {
    "jev-latest": {"input": "0.042", "output": "0"},
    "laya": {"input": "0", "output": "0"},
    "multilingual": {"input": "0", "output": "0"},
    "julia": {"input": "0", "output": "0"},
}
URL_ACTUAL = "https://agentgateway.dev/model-catalog"
URL_ETIQUETA = "https://raw.githubusercontent.com/agentgateway/agentgateway/{v}/catalog/model-catalog.json"


def descargar(url):
    # agentgateway.dev rechaza el User-Agent por defecto de urllib (403).
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def claves_conocidas(catalogo):
    """Conjunto de claves permitidas en cada nivel, aprendido de un catálogo bueno."""
    modelo, tramo, rates, proveedor = set(), set(), set(), set()
    for p in catalogo["providers"].values():
        proveedor |= {k for k in p if k != "models"}
        for m in p["models"].values():
            modelo |= set(m)
            rates |= set(m.get("rates", {}))
            for t in m.get("tiers", []):
                tramo |= set(t)
                rates |= set(t.get("rates", {}))
    return proveedor, modelo, tramo, rates


def adaptar(actual, conocidas):
    proveedor, modelo, tramo, rates = conocidas
    cuenta = {"tramos_quitados": 0, "modelos": 0}
    salida = {"metadata": actual.get("metadata"), "providers": {}}
    for nombre, p in actual["providers"].items():
        p2 = {k: v for k, v in p.items() if k in proveedor and k != "models"}
        p2["models"] = {}
        for mid, m in p["models"].items():
            m2 = {k: v for k, v in m.items() if k in modelo}
            if "rates" in m2:
                m2["rates"] = {k: v for k, v in m2["rates"].items() if k in rates}
            tramos = []
            for t in m.get("tiers", []):
                # Un tramo con cualquier campo desconocido (p. ej. serviceTier
                # "priority"/"flex") es de otro tipo de precio: se omite entero,
                # porque quitarle solo el campo lo dejaría duplicado.
                if "contextOver" not in t or set(t) - tramo:
                    cuenta["tramos_quitados"] += 1
                    continue
                t2 = dict(t)
                t2["rates"] = {k: v for k, v in t.get("rates", {}).items() if k in rates}
                tramos.append(t2)
            if "tiers" in m2:
                if tramos:
                    m2["tiers"] = tramos
                else:
                    del m2["tiers"]
            p2["models"][mid] = m2
            cuenta["modelos"] += 1
        salida["providers"][nombre] = p2
    return salida, cuenta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", default=os.path.join(REPO, "catalog", "model-catalog.compat.json"))
    ap.add_argument("--version", default="v1.6.0", help="etiqueta de agentgateway cuyo formato se respeta")
    a = ap.parse_args()

    actual = descargar(URL_ACTUAL)
    base = descargar(URL_ETIQUETA.format(v=a.version))
    salida, cuenta = adaptar(actual, claves_conocidas(base))
    custom = salida["providers"].setdefault("custom", {"models": {}})
    for modelo, rates in PRECIOS_PROPIOS.items():
        custom["models"][modelo] = {"rates": dict(rates)}

    os.makedirs(os.path.dirname(a.salida), exist_ok=True)
    tmp = a.salida + ".tmp"
    with open(tmp, "w") as f:
        json.dump(salida, f, ensure_ascii=False)
    os.replace(tmp, a.salida)   # atómico: el gateway vigila el fichero
    print(f"Catálogo compatible con {a.version}: {cuenta['modelos']} modelos "
          f"({cuenta['tramos_quitados']} tramos 'serviceTier' omitidos) + "
          f"{len(PRECIOS_PROPIOS)} propios (custom/jev-latest...) -> {a.salida}")


if __name__ == "__main__":
    sys.exit(main())
