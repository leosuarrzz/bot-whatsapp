from datos import guardar_lead, pausar
from whatsapp import avisar_encargado


HORAS_PAUSA = 2


def armar_herramientas(cliente, phone_number_id, numero_persona, nombre_persona):
    """Devuelve las herramientas que la ficha del cliente tiene habilitadas.

    Cada herramienta queda atada a esta conversación: sabe de qué negocio es
    y con quién se está hablando, sin que el modelo tenga que pasarlo.
    """
    ficha = cliente["ficha"]

    def anotar_consulta(interes: str, detalle: str = "",
                        corrige_anterior: bool = False) -> str:
        """Anota la consulta de la persona para que el local la responda después.

        Usala SIEMPRE que la persona pregunte por algo que no podés responder
        con la información que tenés —disponibilidad, precio, un producto
        puntual— y le digas que lo vas a consultar. Si no la usás, nadie en
        el local se entera y la persona espera un aviso que no llega.

        Una llamada por cada cosa distinta que busque: si menciona dos
        productos o dos consultas, usá la herramienta dos veces, una por
        cada una. No las mezcles en un solo registro.

        Args:
            interes: qué está buscando, en pocas palabras.
                Ejemplo: "Nike Jordan 4 talle 43".
            detalle: cualquier dato extra útil de la conversación.
            corrige_anterior: poné True SOLO si la persona está corrigiendo o
                completando la consulta que acabás de anotar recién. Poné False
                si está preguntando por algo distinto, aunque sea la misma
                persona en la misma conversación. En la duda, False: es peor
                perder una consulta que tener dos parecidas.
        """
        guardar_lead(cliente["id"], numero_persona, nombre_persona,
                     interes, detalle, corrige_anterior)

        if ficha.get("numero_encargado") and not corrige_anterior:
            aviso = (
                f"*{ficha['empresa']}* · consulta nueva\n\n"
                f"{nombre_persona} ({numero_persona}) preguntó por:\n"
                f"{interes}"
            )
            if detalle:
                aviso += f"\n\nDetalle: {detalle}"
            aviso += f"\n\nEscribile acá: https://wa.me/{numero_persona}"

            if avisar_encargado(ficha, phone_number_id, aviso):
                print(f"AVISO enviado: {interes}")

        print(f"LEAD guardado (corrige={corrige_anterior}): {interes}")
        return "Consulta anotada correctamente."

    def derivar_a_humano(motivo: str) -> str:
        """Avisa al encargado del local para que atienda la conversación en persona.

        Usala SOLO cuando la persona pide expresamente hablar con alguien,
        está molesta o tiene un reclamo, o el tema es delicado y no se
        resuelve con información. NO la uses para consultas normales de
        precio, stock, horarios o disponibilidad: para eso está
        anotar_consulta.

        Al usarla, el bot deja de responder en esa conversación durante
        2 horas para no interrumpir al encargado.

        Args:
            motivo: en una frase, por qué hace falta que atienda una persona.
                Ejemplo: "pide hablar con el encargado por un reclamo".
        """
        if not ficha.get("numero_encargado"):
            print("No hay numero_encargado en la ficha.")
            return "No hay un contacto configurado para derivar."

        aviso = (
            f"*{ficha['empresa']}* · atención humana\n\n"
            f"{nombre_persona} ({numero_persona}) necesita que lo atiendan.\n"
            f"Motivo: {motivo}\n\n"
            f"Escribile acá: https://wa.me/{numero_persona}"
        )

        if not avisar_encargado(ficha, phone_number_id, aviso):
            return ("No se pudo avisar al encargado. Pedile disculpas y decile "
                    "que se comunique por teléfono con el local.")

        pausar(cliente["id"], numero_persona, HORAS_PAUSA, motivo)

        print(f"DERIVADO: {motivo}")
        return f"Avisado el encargado. El bot queda en silencio {HORAS_PAUSA} horas."

    def pedir_turno(vehiculo: str, trabajo: str, cuando: str,
                    nombre: str = "") -> str:
        """Registra un pedido de turno para que el taller lo confirme después.

        Usala cuando la persona quiere traer el auto y ya te dio las tres
        cosas: qué vehículo es, qué necesita, y qué día y horario le vendría
        bien. Si te falta alguna de las tres, preguntásela antes de usar
        la herramienta.
        Los tres datos pueden venir de mensajes distintos de la conversación.
        Si la persona ya dijo el vehículo o el trabajo antes, usá esos datos
        y no se los vuelvas a pedir. Preguntá solo lo que falte de verdad.

        IMPORTANTE: esto NO confirma el turno ni reserva un lugar. Solo deja
        el pedido anotado para que el taller se comunique y lo confirme.
        Nunca le digas a la persona que el turno ya está confirmado,
        reservado o agendado.
        El horario que pases en cuando tiene que ser uno que la persona
        haya dicho y que esté dentro del horario de atención. Si pidió un
        horario en el que estamos cerrados, no uses la herramienta: decíselo
        primero y esperá a que te confirme otro.
        Args:
            vehiculo: marca, modelo y año. Ejemplo: "VW Gol G4 2012".
            trabajo: qué necesita que le hagan. Ejemplo: "service completo".
            cuando: qué día y horario le viene bien, tal como lo dijo la
                persona. Ejemplo: "el martes a la mañana".
            nombre: cómo se llama, si lo dijo. Si no lo dijo, dejalo vacío.
        """
        faltan = []
        if not vehiculo.strip():
            faltan.append("qué vehículo es")
        if not trabajo.strip():
            faltan.append("qué necesita")
        if not cuando.strip():
            faltan.append("qué día y horario le vendría bien")
        if faltan:
            return ("No se anotó nada. Todavía falta saber " + " y ".join(faltan)
                    + ". Preguntáselo y recién ahí usá la herramienta de nuevo.")

        quien = nombre.strip() or nombre_persona

        guardar_lead(
            cliente["id"],
            numero_persona,
            quien,
            f"TURNO: {trabajo}",
            f"Vehículo: {vehiculo}. Prefiere: {cuando}.",
        )

        if ficha.get("numero_encargado"):
            aviso = (
                f"*{ficha['empresa']}* · PEDIDO DE TURNO\n\n"
                f"{quien} ({numero_persona})\n"
                f"Vehículo: {vehiculo}\n"
                f"Trabajo: {trabajo}\n"
                f"Prefiere: {cuando}\n\n"
                f"Confirmale acá: https://wa.me/{numero_persona}"
            )
            if avisar_encargado(ficha, phone_number_id, aviso):
                print(f"TURNO de {quien}: {trabajo} / {cuando}")

        return ("Pedido de turno anotado. Decile que queda pedido y que el "
                "taller le confirma, sin afirmar que ya está reservado.")

    disponibles = {
        "anotar_consulta": anotar_consulta,
        "derivar_a_humano": derivar_a_humano,
        "pedir_turno": pedir_turno,
    }

    habilitadas = ficha.get("herramientas", list(disponibles))

    return [disponibles[nombre] for nombre in habilitadas
            if nombre in disponibles]
