import sys
from pathlib import Path

from bot import armar_instrucciones, preguntar
from datos import cliente_por_slug

nombre_cliente = sys.argv[1] if len(sys.argv) > 1 else "demo-zapateria"
guion = Path(f"pruebas/{nombre_cliente}.txt")

if not guion.exists():
    print(f"No existe el guion {guion}: una pregunta por línea.")
    raise SystemExit(1)

cliente = cliente_por_slug(nombre_cliente)

if cliente is None:
    print(f"No existe el cliente '{nombre_cliente}' en la base.")
    print("Cargalo con: python -m scripts.cargar_fichas")
    raise SystemExit(1)

ficha = cliente["ficha"]
instrucciones = armar_instrucciones(ficha)

with open(guion, "r", encoding="utf-8") as archivo:
    preguntas = [linea.strip() for linea in archivo if linea.strip()]

print(f"Probando {ficha['empresa']} — {len(preguntas)} preguntas\n")

for numero, pregunta in enumerate(preguntas, start=1):
    historial = [{"role": "user", "parts": [{"text": pregunta}]}]
    respuesta = preguntar(historial, instrucciones)
    print(f"{numero:2d}. Vos: {pregunta}")
    print(f"    {ficha['nombre_bot']}: {respuesta}\n")
