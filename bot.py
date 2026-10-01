import functools
import os
import time
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime
from zoneinfo import ZoneInfo

logging.getLogger("google_genai.models").setLevel(logging.ERROR)

load_dotenv()

ia = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODELOS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]
DIAS = ["lunes", "martes", "miércoles", "jueves",
        "viernes", "sábado", "domingo"]

PLANTILLA = """
Sos {nombre_bot}, la asistente virtual de {empresa}, que se dedica a {rubro}.

TONO
{tono}

LO QUE SABÉS
{datos}

LO QUE NO SABÉS
{limites}

REGLAS
{reglas}
"""


def lista_a_texto(items):
    if isinstance(items, str):
        return "- " + items
    return "\n".join("- " + item for item in items)


def datos_a_texto(diccionario):
    return "\n".join(f"{clave}: {valor}" for clave, valor in diccionario.items())


def momento_actual(ficha):
    zona = ZoneInfo(ficha.get("zona_horaria", "America/Montevideo"))
    ahora = datetime.now(zona)

    return (f"Hoy es {DIAS[ahora.weekday()]} "
            f"{ahora.day}/{ahora.month}/{ahora.year}, "
            f"y son las {ahora.strftime('%H:%M')}.")


def armar_instrucciones(ficha):
    instrucciones = PLANTILLA.format(
        nombre_bot=ficha["nombre_bot"],
        empresa=ficha["empresa"],
        rubro=ficha["rubro"],
        tono=lista_a_texto(ficha["tono"]),
        datos=datos_a_texto(ficha["datos"]),
        limites=lista_a_texto(ficha["limites"]),
        reglas=lista_a_texto(ficha["reglas"]),
    )

    instrucciones += f"""
MOMENTO ACTUAL
{momento_actual(ficha)}
Compará esta hora con el horario de arriba para saber si el local está abierto
o cerrado ahora mismo. Usala también para interpretar "hoy", "mañana" o
"el viernes". Si te preguntan por un día del que no tenés el horario, decilo
en vez de suponer.
"""

    return instrucciones


def preguntar(historial, instrucciones, herramientas=None):
    usadas = []

    if herramientas is not None:
        herramientas = [registrar_uso(h, usadas) for h in herramientas]

    for modelo in MODELOS:
        for intento in range(2):
            try:
                configuracion = types.GenerateContentConfig(
                    system_instruction=instrucciones,
                    tools=herramientas,
                )
                respuesta = ia.models.generate_content(
                    model=modelo,
                    config=configuracion,
                    contents=historial,
                )
            except Exception as error:
                print(f"Falló {modelo} (intento {intento + 1}): {error}")
            else:
                if respuesta.text and respuesta.text.strip():
                    return respuesta.text

                motivo = (respuesta.candidates[0].finish_reason
                          if respuesta.candidates
                          else respuesta.prompt_feedback)
                print(f"{modelo} devolvió una respuesta vacía: {motivo}")

            if usadas:
                # Reintentar volvería a anotar leads y mandar avisos.
                print(f"No reintento: ya se usaron {usadas}")
                return "Listo, quedó registrado."

            time.sleep(2)

    print("TODOS LOS MODELOS FALLARON — revisá la API key y la cuota")
    return "Perdón, no puedo responderte en este momento."


def registrar_uso(herramienta, usadas):
    """Envuelve una herramienta para anotar en usadas cada vez que corre.

    functools.wraps conserva nombre, docstring y firma: Gemini ve la misma
    declaración que con la función original.
    """
    @functools.wraps(herramienta)
    def envoltura(*args, **kwargs):
        usadas.append(herramienta.__name__)
        return herramienta(*args, **kwargs)

    return envoltura


def transcribir(audio, mime_type="audio/ogg"):
    instruccion = (
        "Transcribí este audio a texto, en español rioplatense. "
        "Devolvé únicamente la transcripción, sin comillas ni comentarios. "
        "Si no se entiende nada, devolvé exactamente: [audio inentendible]"
    )

    for modelo in MODELOS:
        for intento in range(2):
            try:
                respuesta = ia.models.generate_content(
                    model=modelo,
                    contents=[
                        types.Part.from_bytes(data=audio, mime_type=mime_type),
                        instruccion,
                    ],
                )
                return respuesta.text.strip()
            except Exception as error:
                print(f"Falló transcribir con {modelo}: {error}")
                time.sleep(2)

    return ""
