import sys
import datos

if len(sys.argv) != 3:
    print("Uso: python -m scripts.olvidar <slug> <telefono>")
    print("Ejemplo: python -m scripts.olvidar demo-taller 59800000000")
    raise SystemExit(1)

slug = sys.argv[1]
telefono = sys.argv[2]

with datos.conectar() as conexion:
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id FROM clientes WHERE slug = %s", (slug,))
        fila = cursor.fetchone()

        if fila is None:
            print(f"No existe el cliente {slug}")
        else:
            cliente_id = fila[0]

            cursor.execute(
                "DELETE FROM mensajes WHERE cliente_id = %s AND telefono = %s",
                (cliente_id, telefono),
            )
            print(f"Mensajes borrados: {cursor.rowcount}")

            cursor.execute(
                "DELETE FROM leads WHERE cliente_id = %s AND telefono = %s",
                (cliente_id, telefono),
            )
            print(f"Leads borrados: {cursor.rowcount}")

            cursor.execute(
                "DELETE FROM pausas WHERE cliente_id = %s AND telefono = %s",
                (cliente_id, telefono),
            )
            print(f"Pausas borradas: {cursor.rowcount}")

    conexion.commit()
