import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conexion:
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT c.slug, m.telefono, m.rol, m.texto, m.creado_en
            FROM mensajes m
            JOIN clientes c ON c.id = m.cliente_id
            ORDER BY m.creado_en DESC
            LIMIT 20
        """)

        for slug, telefono, rol, texto, creado in cursor.fetchall():
            quien = "cliente" if rol == "user" else "bot"
            print(f"[{creado:%H:%M}] {slug} · {telefono} · {quien}: {texto[:70]}")
