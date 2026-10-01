import os

import psycopg
from dotenv import load_dotenv


load_dotenv()

URL = os.getenv("DATABASE_URL")


def conectar():
    return psycopg.connect(URL)


def cliente_por_numero(phone_number_id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, slug, ficha
                FROM clientes
                WHERE phone_number_id = %s AND activo = TRUE
                """,
                (phone_number_id,),
            )
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {"id": fila[0], "slug": fila[1], "ficha": fila[2]}


def cliente_por_slug(slug):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id, slug, ficha FROM clientes WHERE slug = %s",
                (slug,),
            )
            fila = cursor.fetchone()

    if fila is None:
        return None

    return {"id": fila[0], "slug": fila[1], "ficha": fila[2]}


def guardar_mensaje(cliente_id, telefono, rol, texto, wa_id=None):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO mensajes (cliente_id, telefono, rol, texto, wa_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (wa_id) DO NOTHING
                """,
                (cliente_id, telefono, rol, texto, wa_id),
            )
            guardado = cursor.rowcount > 0
        conexion.commit()

    return guardado


def historial(cliente_id, telefono, limite=20):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT rol, texto FROM (
                    SELECT rol, texto, creado_en
                    FROM mensajes
                    WHERE cliente_id = %s AND telefono = %s
                    ORDER BY creado_en DESC
                    LIMIT %s
                ) AS ultimos
                ORDER BY creado_en ASC
                """,
                (cliente_id, telefono, limite),
            )
            filas = cursor.fetchall()

    return [{"role": rol, "parts": [{"text": texto}]} for rol, texto in filas]


def guardar_lead(cliente_id, telefono, nombre, interes, detalle, corrige=False):
    with conectar() as conexion:
        with conexion.cursor() as cursor:

            if corrige:
                cursor.execute(
                    """
                    UPDATE leads
                    SET interes = %s, detalle = %s, nombre = %s
                    WHERE id = (
                        SELECT id FROM leads
                        WHERE cliente_id = %s
                          AND telefono = %s
                          AND estado = 'nuevo'
                        ORDER BY creado_en DESC
                        LIMIT 1
                    )
                    """,
                    (interes, detalle, nombre, cliente_id, telefono),
                )

                if cursor.rowcount > 0:
                    conexion.commit()
                    return

            cursor.execute(
                """
                INSERT INTO leads (cliente_id, telefono, nombre, interes, detalle)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (cliente_id, telefono, nombre, interes, detalle),
            )

        conexion.commit()


def pausar(cliente_id, telefono, horas, motivo):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pausas (cliente_id, telefono, hasta, motivo)
                VALUES (%s, %s, now() + make_interval(hours => %s), %s)
                ON CONFLICT (cliente_id, telefono) DO UPDATE
                SET hasta = EXCLUDED.hasta, motivo = EXCLUDED.motivo
                """,
                (cliente_id, telefono, horas, motivo),
            )
        conexion.commit()


def esta_pausada(cliente_id, telefono):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM pausas
                WHERE cliente_id = %s AND telefono = %s AND hasta > now()
                """,
                (cliente_id, telefono),
            )
            return cursor.fetchone() is not None


def ya_procesado(wa_id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT 1 FROM mensajes WHERE wa_id = %s", (wa_id,))
            return cursor.fetchone() is not None


def es_ultimo_mensaje(cliente_id, telefono, wa_id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT wa_id FROM mensajes
                WHERE cliente_id = %s AND telefono = %s AND rol = 'user'
                ORDER BY creado_en DESC
                LIMIT 1
                """,
                (cliente_id, telefono),
            )
            fila = cursor.fetchone()

    return fila is not None and fila[0] == wa_id
