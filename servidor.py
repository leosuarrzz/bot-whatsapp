import os
import json
import hmac
import hashlib
import logging
import time

from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv
from bot import armar_instrucciones, preguntar, transcribir
from datos import (
    cliente_por_numero,
    es_ultimo_mensaje,
    esta_pausada,
    guardar_mensaje,
    historial,
    ya_procesado,
)
from herramientas import armar_herramientas
from whatsapp import bajar_media, enviar_whatsapp, marcar_leido

logging.getLogger("google_genai.models").setLevel(logging.ERROR)

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")

ESPERA_SEGUNDOS = 6

app = FastAPI()


def firma_valida(cuerpo, cabecera):
    if not APP_SECRET or not cabecera.startswith("sha256="):
        return False

    esperado = hmac.new(
        APP_SECRET.encode(),
        cuerpo,
        hashlib.sha256,
    ).hexdigest()

    recibida = cabecera.split("=", 1)[1]

    return hmac.compare_digest(esperado, recibida)


@app.get("/")
def vivo():
    return {"estado": "vivo"}


@app.get("/webhook")
def verificar(request: Request):
    parametros = request.query_params

    if (parametros.get("hub.mode") == "subscribe"
            and parametros.get("hub.verify_token") == VERIFY_TOKEN):
        return Response(content=parametros.get("hub.challenge"),
                        media_type="text/plain")

    return Response(content="token invalido", status_code=403)


def instrucciones_de_conversacion(ficha, nombre_persona, numero_persona):
    return armar_instrucciones(ficha) + f"""

CONTEXTO DE ESTA CONVERSACIÓN
La persona se llama {nombre_persona} y su teléfono es {numero_persona}.
Ya tenés esos datos: no se los pidas nunca. Usá su nombre con naturalidad.
"""


def atender(phone_number_id, message_id, numero_persona, nombre_persona,
            texto, audio_id=None):

    # Filtro rápido para reintentos tardíos de Meta. El candado real es el
    # INSERT de guardar_mensaje, más abajo.
    if ya_procesado(message_id):
        print("Mensaje repetido, ignorado:", message_id)
        return

    cliente = cliente_por_numero(phone_number_id)

    if cliente is None:
        print("Número no registrado:", phone_number_id)
        return

    # En pausa el mensaje se guarda igual, para que el bot tenga el contexto
    # cuando vuelva a responder. No se marca como leído: el indicador de
    # "escribiendo" haría creer que el bot va a contestar.
    pausada = esta_pausada(cliente["id"], numero_persona)

    if not pausada:
        marcar_leido(phone_number_id, message_id)

    if audio_id:
        audio, mime = bajar_media(audio_id)

        if audio is None:
            texto = "[la persona mandó un audio que no se pudo procesar]"
        else:
            texto = transcribir(audio, mime)
            print(f"TRANSCRIPCIÓN: {texto}")

    if not texto:
        return

    # Candado contra entregas simultáneas del mismo mensaje: el índice único
    # en wa_id hace que solo un INSERT gane; el resto recibe False y corta.
    if not guardar_mensaje(cliente["id"], numero_persona, "user", texto,
                           message_id):
        print("Mensaje repetido, otra tarea ya lo está atendiendo:",
              message_id)
        return

    if pausada:
        print("Conversación pausada: mensaje guardado, el bot no responde.")
        return

    time.sleep(ESPERA_SEGUNDOS)

    if not es_ultimo_mensaje(cliente["id"], numero_persona, message_id):
        print("Llegó otro mensaje después: este turno se descarta.")
        return

    ficha = cliente["ficha"]

    respuesta = preguntar(
        historial(cliente["id"], numero_persona),
        instrucciones_de_conversacion(ficha, nombre_persona, numero_persona),
        armar_herramientas(cliente, phone_number_id,
                           numero_persona, nombre_persona),
    )

    guardar_mensaje(cliente["id"], numero_persona, "model", respuesta)

    print(f"{ficha['nombre_bot']}: {respuesta}")
    enviar_whatsapp(phone_number_id, numero_persona, respuesta)


def registrar_fallidos(estados):
    for estado in estados:
        if estado.get("status") != "failed":
            continue

        for error in estado.get("errors", [{}]):
            print(f"ENVÍO FALLIDO a {estado.get('recipient_id')}: "
                  f"{error.get('code')} {error.get('title')}")

            if error.get("code") == 131047:
                print("  Pasaron más de 24 horas desde el último mensaje de "
                      "ese número: Meta solo acepta una plantilla aprobada.")


@app.post("/webhook")
async def recibir(request: Request, tareas: BackgroundTasks):
    cuerpo = await request.body()
    firma = request.headers.get("x-hub-signature-256", "")

    if not firma_valida(cuerpo, firma):
        print("Firma inválida: mensaje descartado")
        return Response(content="firma invalida", status_code=403)

    datos = json.loads(cuerpo)

    try:
        valor = datos["entry"][0]["changes"][0]["value"]
    except (KeyError, IndexError):
        return {"ok": True}

    registrar_fallidos(valor.get("statuses", []))

    if "messages" not in valor:
        return {"ok": True}

    mensaje = valor["messages"][0]

    tipo = mensaje.get("type")

    if tipo not in ("text", "audio"):
        return {"ok": True}

    texto = mensaje["text"]["body"] if tipo == "text" else None
    audio_id = mensaje["audio"]["id"] if tipo == "audio" else None

    phone_number_id = valor["metadata"]["phone_number_id"]
    numero_persona = mensaje["from"]

    contactos = valor.get("contacts", [{}])
    nombre_persona = contactos[0].get("profile", {}).get("name", "")

    print(f"[{nombre_persona} · {numero_persona}] {tipo}: {texto or audio_id}")

    tareas.add_task(atender, phone_number_id, mensaje["id"],
                    numero_persona, nombre_persona, texto, audio_id)

    return {"ok": True}
