import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conexion:
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT c.slug, l.creado_en, l.nombre, l.telefono,
                   l.interes, l.detalle, l.estado
            FROM leads l
            JOIN clientes c ON c.id = l.cliente_id
            ORDER BY l.creado_en DESC
            LIMIT 20
        """)

        filas = cursor.fetchall()

if not filas:
    print("Todavía no hay leads.")

for slug, creado, nombre, telefono, interes, detalle, estado in filas:
    print(f"[{creado:%d/%m %H:%M}] {slug} · {estado}")
    print(f"   {nombre} ({telefono})")
    print(f"   Busca: {interes}")
    if detalle:
        print(f"   Nota: {detalle}")
    print()
