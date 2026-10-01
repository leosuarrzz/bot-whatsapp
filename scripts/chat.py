import sys

from bot import armar_instrucciones, preguntar
from datos import cliente_por_slug

slug = sys.argv[1] if len(sys.argv) > 1 else "demo-zapateria"

cliente = cliente_por_slug(slug)

if cliente is None:
    print(f"No existe el cliente '{slug}' en la base.")
    raise SystemExit(1)

ficha = cliente["ficha"]
instrucciones = armar_instrucciones(ficha)

historial = []

print(f"Hablando con {ficha['nombre_bot']} de {ficha['empresa']}.")
print("Escribí 'salir' para terminar.\n")

while True:
    mensaje = input("Vos: ").strip()

    if not mensaje:
        continue

    if mensaje.lower() in ("salir", "chau", "exit", "q"):
        break

    historial.append({"role": "user", "parts": [{"text": mensaje}]})

    texto = preguntar(historial, instrucciones)
    print(f"{ficha['nombre_bot']}:", texto, "\n")

    historial.append({"role": "model", "parts": [{"text": texto}]})
