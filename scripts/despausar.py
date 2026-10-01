import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(os.getenv("DATABASE_URL")) as conexion:
    with conexion.cursor() as cursor:
        cursor.execute("DELETE FROM pausas")
        borradas = cursor.rowcount
    conexion.commit()

print(f"Pausas levantadas: {borradas}")
