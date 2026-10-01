import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

SQL = """
CREATE TABLE IF NOT EXISTS clientes (
    id              SERIAL PRIMARY KEY,
    slug            TEXT UNIQUE NOT NULL,
    phone_number_id TEXT UNIQUE NOT NULL,
    ficha           JSONB NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mensajes (
    id         BIGSERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    telefono   TEXT NOT NULL,
    rol        TEXT NOT NULL,
    texto      TEXT NOT NULL,
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mensajes_conversacion
    ON mensajes (cliente_id, telefono, creado_en);

CREATE TABLE IF NOT EXISTS leads (
    id         SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    telefono   TEXT NOT NULL,
    nombre     TEXT,
    interes    TEXT NOT NULL,
    detalle    TEXT,
    estado     TEXT NOT NULL DEFAULT 'nuevo',
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS wa_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mensajes_wa_id ON mensajes (wa_id);
CREATE TABLE IF NOT EXISTS pausas (
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    telefono   TEXT NOT NULL,
    hasta      TIMESTAMPTZ NOT NULL,
    motivo     TEXT,
    PRIMARY KEY (cliente_id, telefono)
);

"""

with psycopg.connect(os.getenv("DATABASE_URL")) as conexion:
    with conexion.cursor() as cursor:
        cursor.execute(SQL)
    conexion.commit()

print("Tablas creadas.")
