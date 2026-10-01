import json
import os
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv

load_dotenv()

SQL = """
INSERT INTO clientes (slug, phone_number_id, ficha)
VALUES (%s, %s, %s)
ON CONFLICT (slug) DO UPDATE
SET phone_number_id = EXCLUDED.phone_number_id,
    ficha = EXCLUDED.ficha;
"""

with psycopg.connect(os.getenv("DATABASE_URL")) as conexion:
    with conexion.cursor() as cursor:

        for ruta in Path("clientes").glob("*.yaml"):
            with open(ruta, "r", encoding="utf-8") as archivo:
                ficha = yaml.safe_load(archivo)

            slug = ruta.stem
            phone_number_id = str(ficha["phone_number_id"])

            cursor.execute(SQL, (slug, phone_number_id, json.dumps(ficha)))
            print("Cargado:", slug, "->", phone_number_id)

    conexion.commit()
