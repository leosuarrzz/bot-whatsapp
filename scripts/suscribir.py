import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_TOKEN")

waba_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv("WABA_ID")

if not waba_id:
    print("Falta el identificador de la cuenta de WhatsApp.")
    print("Uso: python suscribir.py <waba_id>")
    raise SystemExit(1)

url = f"https://graph.facebook.com/v26.0/{waba_id}/subscribed_apps"

respuesta = requests.post(url, headers={"Authorization": f"Bearer {TOKEN}"})

print(f"Cuenta: {waba_id}")
print(respuesta.status_code)
print(respuesta.text)
