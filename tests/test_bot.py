from datetime import datetime
from types import SimpleNamespace

import pytest
from google.genai import types

import bot
import herramientas


def test_lista_a_texto_con_lista():
    assert bot.lista_a_texto(["uno", "dos"]) == "- uno\n- dos"


def test_lista_a_texto_con_texto_corrido():
    assert bot.lista_a_texto("Tuteá siempre.") == "- Tuteá siempre."


def test_lista_a_texto_vacia():
    assert bot.lista_a_texto([]) == ""


class RelojFijo(datetime):
    """datetime cuyo now() devuelve siempre el mismo momento."""
    zona_pedida = None

    @classmethod
    def now(cls, tz=None):
        cls.zona_pedida = tz
        return cls(2026, 9, 25, 9, 5, tzinfo=tz)


def test_momento_actual(monkeypatch):
    monkeypatch.setattr(bot, "datetime", RelojFijo)

    texto = bot.momento_actual({"zona_horaria": "Europe/Madrid"})

    assert texto == "Hoy es viernes 25/9/2026, y son las 09:05."
    assert str(RelojFijo.zona_pedida) == "Europe/Madrid"


def test_momento_actual_usa_montevideo_por_defecto(monkeypatch):
    monkeypatch.setattr(bot, "datetime", RelojFijo)

    bot.momento_actual({})

    assert str(RelojFijo.zona_pedida) == "America/Montevideo"


# --- preguntar: reintentos y herramientas ---


class GeminiFalso:
    """Cliente de Gemini falso: cada llamada ejecuta un paso del guion."""

    def __init__(self, *pasos):
        self.pasos = list(pasos)
        self.llamadas = 0
        self.models = self

    def generate_content(self, model, config, contents):
        self.llamadas += 1
        return self.pasos.pop(0)(config.tools or [])


def responde(texto):
    return lambda tools: SimpleNamespace(
        text=texto, candidates=[SimpleNamespace(finish_reason="STOP")])


def falla(tools):
    raise RuntimeError("error de la API")


def usa_herramienta_y_falla(tools):
    tools[0]()
    raise RuntimeError("se cortó después de la herramienta")


@pytest.fixture
def sin_esperas(monkeypatch):
    monkeypatch.setattr(bot.time, "sleep", lambda s: None)


def test_reintenta_si_falla_antes_de_usar_herramientas(monkeypatch,
                                                       sin_esperas):
    gemini = GeminiFalso(falla, responde("hola"))
    monkeypatch.setattr(bot, "ia", gemini)

    assert bot.preguntar([], "instrucciones", []) == "hola"
    assert gemini.llamadas == 2


def test_no_reintenta_si_ya_uso_una_herramienta(monkeypatch, sin_esperas):
    ejecuciones = []

    def anotar_consulta() -> str:
        """Anota una consulta."""
        ejecuciones.append(1)
        return "ok"

    gemini = GeminiFalso(usa_herramienta_y_falla, responde("no debería"))
    monkeypatch.setattr(bot, "ia", gemini)

    respuesta = bot.preguntar([], "instrucciones", [anotar_consulta])

    assert respuesta == "Listo, quedó registrado."
    assert ejecuciones == [1]
    assert gemini.llamadas == 1


def test_respuesta_vacia_sin_herramientas_pasa_al_siguiente(monkeypatch,
                                                            sin_esperas):
    gemini = GeminiFalso(responde(None), responde("hola"))
    monkeypatch.setattr(bot, "ia", gemini)

    assert bot.preguntar([], "instrucciones") == "hola"


def test_la_envoltura_no_cambia_lo_que_ve_gemini():
    cliente = {"id": 1, "slug": "demo", "ficha": {"empresa": "Demo"}}
    originales = herramientas.armar_herramientas(cliente, "1", "598", "Ana")

    for original in originales:
        envuelta = bot.registrar_uso(original, [])
        declarar = types.FunctionDeclaration.from_callable_with_api_option
        assert (declarar(callable=envuelta).model_dump()
                == declarar(callable=original).model_dump())
