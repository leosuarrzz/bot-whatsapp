import sys
import datos

if len(sys.argv) != 3:
    print("Uso: python -m scripts.liberar <slug> <phone_number_id>")
    print("Ejemplo: python -m scripts.liberar demo-taller 000000000000001")
    raise SystemExit(1)

slug = sys.argv[1]
nuevo = sys.argv[2]

with datos.conectar() as conexion:
    with conexion.cursor() as cursor:
        cursor.execute(
            "UPDATE clientes SET phone_number_id = %s WHERE slug = %s",
            (nuevo, slug),
        )
        print(f"Filas cambiadas: {cursor.rowcount}")

        if cursor.rowcount == 0:
            print(f"No existe el cliente '{slug}' en la base.")
    conexion.commit()
