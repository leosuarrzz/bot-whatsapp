import os

import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")

GRAPH = "https://graph.facebook.com/v26.0"
TIMEOUT = 15


def cabeceras():
    return {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}


def api_whatsapp(phone_number_id, cuerpo):
    return requests.post(
        f"{GRAPH}/{phone_number_id}/messages",
        json=cuerpo,
        headers=cabeceras(),
        timeout=TIMEOUT,
    )


def marcar_leido(phone_number_id, message_id):
    try:
        api_whatsapp(phone_number_id, {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
            "typing_indicator": {"type": "text"},
        })
    except requests.RequestException as error:
        print(f"No se pudo marcar como leído: {error}")


def enviar_whatsapp(phone_number_id, destino, texto):
    """Manda un texto. Devuelve True solo si Meta aceptó el envío."""
    try:
        respuesta = api_whatsapp(phone_number_id, {
            "messaging_product": "whatsapp",
            "to": destino,
            "text": {"body": texto},
        })
    except requests.RequestException as error:
        print(f"envío a {destino} falló: {error}")
        return False

    print("envío:", respuesta.status_code, respuesta.text)
    return respuesta.ok


def avisar_encargado(ficha, phone_number_id, texto):
    """Manda un aviso al encargado del local. Devuelve True si salió.

    Ojo: Meta puede aceptar el envío y rechazarlo después (error 131047,
    fuera de la ventana de 24 horas). Eso llega como un estado "failed" en
    el webhook y se muestra en los logs desde recibir().
    """
    encargado = ficha.get("numero_encargado")

    if not encargado:
        print("No hay numero_encargado en la ficha.")
        return False

    if not enviar_whatsapp(phone_number_id, encargado, texto):
        print(f"No se pudo avisar al encargado {encargado}.")
        return False

    return True


def bajar_media(media_id):
    try:
        datos = requests.get(
            f"{GRAPH}/{media_id}",
            headers=cabeceras(),
            timeout=TIMEOUT,
        ).json()

        url = datos.get("url")

        if not url:
            print("No se pudo obtener el archivo:", datos)
            return None, None

        archivo = requests.get(url, headers=cabeceras(), timeout=TIMEOUT)
    except requests.RequestException as error:
        print(f"No se pudo bajar el archivo: {error}")
        return None, None

    mime = datos.get("mime_type", "audio/ogg").split(";")[0].strip()

    return archivo.content, mime
