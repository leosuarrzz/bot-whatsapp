import pytest

import herramientas

FICHA = {"empresa": "Taller Demo", "numero_encargado": "598XXXXXXXX"}


def armar(ficha):
    cliente = {"id": 1, "slug": "demo-taller", "ficha": ficha}
    return herramientas.armar_herramientas(
        cliente, "000000000000001", "59800000000", "Ana")


def nombres(lista):
    return [herramienta.__name__ for herramienta in lista]


@pytest.fixture
def registro(monkeypatch):
    """Reemplaza la base y WhatsApp por listas que anotan las llamadas."""
    llamadas = {"leads": [], "avisos": [], "pausas": []}
    monkeypatch.setattr(herramientas, "guardar_lead",
                        lambda *a, **k: llamadas["leads"].append(a))
    monkeypatch.setattr(herramientas, "pausar",
                        lambda *a, **k: llamadas["pausas"].append(a))
    monkeypatch.setattr(herramientas, "avisar_encargado",
                        lambda *a, **k: llamadas["avisos"].append(a) or True)
    return llamadas


def test_respeta_las_herramientas_habilitadas():
    ficha = dict(FICHA, herramientas=["anotar_consulta", "pedir_turno"])
    assert nombres(armar(ficha)) == ["anotar_consulta", "pedir_turno"]


def test_sin_lista_habilita_todas():
    assert nombres(armar(FICHA)) == [
        "anotar_consulta", "derivar_a_humano", "pedir_turno"]


def test_lista_vacia_no_habilita_ninguna():
    assert armar(dict(FICHA, herramientas=[])) == []


def test_ignora_nombres_desconocidos():
    ficha = dict(FICHA, herramientas=["derivar_a_humano", "no_existe"])
    assert nombres(armar(ficha)) == ["derivar_a_humano"]


def pedir_turno():
    ficha = dict(FICHA, herramientas=["pedir_turno"])
    return armar(ficha)[0]


@pytest.mark.parametrize("vehiculo, trabajo, cuando, falta", [
    ("", "service", "el martes", "qué vehículo es"),
    ("Gol 2012", "", "el martes", "qué necesita"),
    ("Gol 2012", "service", "", "qué día y horario"),
    ("  ", "service", "el martes", "qué vehículo es"),
])
def test_pedir_turno_no_anota_si_falta_un_dato(registro, vehiculo, trabajo,
                                               cuando, falta):
    resultado = pedir_turno()(vehiculo, trabajo, cuando)

    assert resultado.startswith("No se anotó nada")
    assert falta in resultado
    assert registro["leads"] == []
    assert registro["avisos"] == []


def test_pedir_turno_anota_con_los_tres_datos(registro):
    resultado = pedir_turno()("Gol 2012", "service", "el martes a la mañana")

    assert resultado.startswith("Pedido de turno anotado")
    assert len(registro["leads"]) == 1
    assert registro["leads"][0][3] == "TURNO: service"
    assert len(registro["avisos"]) == 1


def test_derivar_no_pausa_si_el_aviso_falla(registro, monkeypatch):
    monkeypatch.setattr(herramientas, "avisar_encargado", lambda *a: False)
    derivar = armar(dict(FICHA, herramientas=["derivar_a_humano"]))[0]

    resultado = derivar("pide hablar con el encargado")

    assert resultado.startswith("No se pudo avisar")
    assert registro["pausas"] == []
