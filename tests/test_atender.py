import threading

import pytest

import servidor

CLIENTE = {"id": 1, "slug": "demo-taller",
           "ficha": {"empresa": "Taller Demo", "nombre_bot": "Lucía"}}


def base_falsa(llamadas):
    """guardar_mensaje falso que imita el índice único sobre wa_id."""
    candado = threading.Lock()
    ids = set()

    def guardar_mensaje(*args):
        wa_id = args[4] if len(args) > 4 else None
        with candado:
            if wa_id is not None and wa_id in ids:
                return False
            if wa_id is not None:
                ids.add(wa_id)
            llamadas["guardados"].append(args)
            return True

    return guardar_mensaje


@pytest.fixture
def registro(monkeypatch):
    """Reemplaza la base, WhatsApp y Gemini por funciones que anotan."""
    llamadas = {"guardados": [], "leidos": [], "enviados": [], "preguntas": 0}

    def preguntar(*a):
        llamadas["preguntas"] += 1
        return "respuesta"

    monkeypatch.setattr(servidor, "ESPERA_SEGUNDOS", 0)
    monkeypatch.setattr(servidor, "ya_procesado", lambda wa_id: False)
    monkeypatch.setattr(servidor, "cliente_por_numero", lambda p: CLIENTE)
    monkeypatch.setattr(servidor, "esta_pausada", lambda c, t: False)
    monkeypatch.setattr(servidor, "es_ultimo_mensaje", lambda *a: True)
    monkeypatch.setattr(servidor, "historial", lambda c, t: [])
    monkeypatch.setattr(servidor, "armar_instrucciones", lambda f: "")
    monkeypatch.setattr(servidor, "armar_herramientas", lambda *a: [])
    monkeypatch.setattr(servidor, "preguntar", preguntar)
    monkeypatch.setattr(servidor, "guardar_mensaje", base_falsa(llamadas))
    monkeypatch.setattr(servidor, "marcar_leido",
                        lambda *a: llamadas["leidos"].append(a))
    monkeypatch.setattr(servidor, "enviar_whatsapp",
                        lambda *a: llamadas["enviados"].append(a))
    return llamadas


def atender():
    servidor.atender("000000000000001", "wamid.1", "59800000000", "Ana",
                     "hola")


def test_responde_si_no_esta_pausada(registro):
    atender()

    assert [g[2] for g in registro["guardados"]] == ["user", "model"]
    assert len(registro["leidos"]) == 1
    assert len(registro["enviados"]) == 1


def test_en_pausa_guarda_el_mensaje_pero_no_responde(registro, monkeypatch):
    monkeypatch.setattr(servidor, "esta_pausada", lambda c, t: True)

    atender()

    assert registro["guardados"] == [
        (1, "59800000000", "user", "hola", "wamid.1")]
    assert registro["leidos"] == []
    assert registro["enviados"] == []
    assert registro["preguntas"] == 0


def test_mensaje_ya_guardado_no_se_responde(registro, monkeypatch):
    monkeypatch.setattr(servidor, "guardar_mensaje", lambda *a: False)

    atender()

    assert registro["enviados"] == []
    assert registro["preguntas"] == 0


def test_dos_entregas_simultaneas_responden_una_sola_vez(registro,
                                                         monkeypatch):
    # Las dos tareas pasan juntas el filtro de ya_procesado, como pasa
    # cuando Meta entrega el mismo mensaje dos veces casi a la vez.
    barrera = threading.Barrier(2, timeout=5)

    def ya_procesado(wa_id):
        barrera.wait()
        return False

    monkeypatch.setattr(servidor, "ya_procesado", ya_procesado)

    tareas = [threading.Thread(target=atender) for _ in range(2)]
    for tarea in tareas:
        tarea.start()
    for tarea in tareas:
        tarea.join(timeout=5)

    assert len(registro["enviados"]) == 1
    assert registro["preguntas"] == 1
    assert [g[2] for g in registro["guardados"]] == ["user", "model"]
