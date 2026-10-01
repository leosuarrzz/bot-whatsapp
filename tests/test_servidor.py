import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

import servidor

SECRETO = "secreto-de-prueba"
CUERPO = b'{"entry": []}'


def firmar(cuerpo, secreto=SECRETO):
    return hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def configuracion(monkeypatch):
    monkeypatch.setattr(servidor, "APP_SECRET", SECRETO)
    monkeypatch.setattr(servidor, "VERIFY_TOKEN", "token-de-prueba")


def test_firma_correcta():
    assert servidor.firma_valida(CUERPO, "sha256=" + firmar(CUERPO))


def test_firma_incorrecta():
    otra = firmar(CUERPO, secreto="otro-secreto")
    assert not servidor.firma_valida(CUERPO, "sha256=" + otra)


def test_firma_de_otro_cuerpo():
    assert not servidor.firma_valida(CUERPO, "sha256=" + firmar(b"{}"))


def test_firma_sin_prefijo_sha256():
    assert not servidor.firma_valida(CUERPO, firmar(CUERPO))


def test_firma_sin_app_secret(monkeypatch):
    monkeypatch.setattr(servidor, "APP_SECRET", None)
    assert not servidor.firma_valida(CUERPO, "sha256=" + firmar(CUERPO))


def test_webhook_rechaza_firma_invalida():
    cliente = TestClient(servidor.app)
    respuesta = cliente.post("/webhook", content=CUERPO,
                             headers={"x-hub-signature-256": "sha256=00"})
    assert respuesta.status_code == 403


def test_verificacion_webhook_con_token_correcto():
    cliente = TestClient(servidor.app)
    respuesta = cliente.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "token-de-prueba",
        "hub.challenge": "1234567",
    })
    assert respuesta.status_code == 200
    assert respuesta.text == "1234567"
    assert respuesta.headers["content-type"].startswith("text/plain")


def test_verificacion_webhook_con_token_incorrecto():
    cliente = TestClient(servidor.app)
    respuesta = cliente.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "otro-token",
        "hub.challenge": "1234567",
    })
    assert respuesta.status_code == 403
    assert "1234567" not in respuesta.text
