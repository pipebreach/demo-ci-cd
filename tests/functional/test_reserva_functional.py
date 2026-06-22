"""Step definitions funcionales para el sistema de reserva de salas."""

import httpx
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/reserva.feature")

SALAS_ESPERADAS = {"A": 4, "B": 8, "C": 20}
HORARIO_INICIO = "08:00"
HORARIO_FIN = "20:00"


# ============================================================
# Antecedentes (Background)
# ============================================================


@given("que el sistema gestiona las siguientes salas con sus capacidades máximas:")
def sistema_gestiona_salas(datatable: list[list[str]], api_client: httpx.Client) -> None:
    """Verifica que la API gestiona las salas y capacidades declaradas en la datatable."""
    assert datatable[0] == ["sala", "capacidad"], f"Header inesperado: {datatable[0]}"
    salas_vistas: set[str] = set()
    for fila in datatable[1:]:
        sala, capacidad = fila[0], int(fila[1])
        assert sala in SALAS_ESPERADAS, f"Sala inesperada en datatable: {sala}"
        assert capacidad == SALAS_ESPERADAS[sala], (
            f"Capacidad incorrecta para sala {sala}: esperada {SALAS_ESPERADAS[sala]}"
        )
        assert sala not in salas_vistas, f"Sala duplicada en datatable: {sala}"
        salas_vistas.add(sala)
    assert salas_vistas == set(SALAS_ESPERADAS), (
        f"Salas incompletas. Esperadas: {set(SALAS_ESPERADAS)}, vistas: {salas_vistas}"
    )
    response = api_client.get("/api/v1/salas")
    assert response.status_code == 200, f"GET /api/v1/salas falló: {response.status_code}"
    datos_api = response.json()
    salas_api = {s["sala"]: s["capacidad"] for s in datos_api}
    assert set(salas_api.keys()) == set(SALAS_ESPERADAS), (
        f"Conjunto de salas incorrecto. "
        f"Esperado: {set(SALAS_ESPERADAS)}, obtenido: {set(salas_api.keys())}"
    )
    for sala, capacidad in SALAS_ESPERADAS.items():
        assert salas_api[sala] == capacidad, f"Capacidad incorrecta en API para sala {sala}"


@given(
    parsers.parse(
        'que el horario laboral permitido para reservas es de "{hora_inicio}" a "{hora_fin}"'
    )
)
def horario_laboral_definido(hora_inicio: str, hora_fin: str, api_client: httpx.Client) -> None:
    """Verifica que la API está activa y registra el horario laboral esperado."""
    assert hora_inicio == HORARIO_INICIO, f"Hora inicio inesperada: {hora_inicio}"
    assert hora_fin == HORARIO_FIN, f"Hora fin inesperada: {hora_fin}"
    response = api_client.get("/health")
    assert response.status_code == 200, f"Health check falló: {response.status_code}"


# ============================================================
# Given steps
# ============================================================


@given(parsers.parse('que no existen reservas para la sala "{sala}"'))
def no_existen_reservas_sala(sala: str, api_client: httpx.Client) -> None:
    """Limpia todas las reservas existentes para la sala especificada."""
    response = api_client.get("/api/v1/reservas", params={"sala": sala})
    assert response.status_code == 200
    for item in response.json():
        del_resp = api_client.delete(f"/api/v1/reservas/{item['id']}")
        assert del_resp.status_code in (200, 204), (
            f"No se pudo eliminar reserva {item['id']}: {del_resp.status_code}"
        )
    response = api_client.get("/api/v1/reservas", params={"sala": sala})
    assert response.status_code == 200, (
        f"GET /api/v1/reservas tras limpieza falló para sala {sala}: {response.status_code}"
    )
    assert response.json() == [], (
        f"No se pudieron limpiar todas las reservas de sala {sala}: {response.json()}"
    )


@given(
    parsers.parse(
        'que existe una reserva para la sala "{sala}" el día "{fecha}"'
        ' de "{hora_inicio}" a "{hora_fin}" con {asistentes:d} asistentes'
        ' y propósito "{proposito}"'
    )
)
def existe_reserva(
    sala: str,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    api_client: httpx.Client,
    context: dict,
) -> None:
    """Crea una reserva si no existe aún (check-before-create idempotente)."""
    listado = api_client.get("/api/v1/reservas", params={"sala": sala})
    assert listado.status_code == 200
    existentes = [
        r
        for r in listado.json()
        if r["sala"] == sala
        and r["fecha"] == fecha
        and r["hora_inicio"] == hora_inicio
        and r["hora_fin"] == hora_fin
        and r["asistentes"] == asistentes
        and r["proposito"] == proposito
    ]
    if existentes:
        context["reserva_id"] = existentes[0]["id"]
        return
    payload = {
        "sala": sala,
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "asistentes": asistentes,
        "proposito": proposito,
    }
    response = api_client.post("/api/v1/reservas", json=payload)
    assert response.status_code == 201, (
        f"No se pudo crear la reserva de precondición: {response.text}"
    )
    context["reserva_id"] = response.json()["id"]


# ============================================================
# When steps
# ============================================================


@when(
    parsers.parse(
        'se crea una reserva para la sala "{sala}" el día "{fecha}"'
        ' de "{hora_inicio}" a "{hora_fin}" con {asistentes:d} asistentes'
        ' y propósito "{proposito}"'
    )
)
def crear_reserva(
    sala: str,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    api_client: httpx.Client,
    context: dict,
) -> None:
    """Envía una solicitud de creación de reserva al sistema."""
    payload = {
        "sala": sala,
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "asistentes": asistentes,
        "proposito": proposito,
    }
    context["last_payload"] = payload
    context["last_response"] = api_client.post("/api/v1/reservas", json=payload)


@when(
    parsers.parse(
        'se intenta crear una reserva para la sala "{sala}" el día "{fecha}"'
        ' de "{hora_inicio}" a "{hora_fin}" con {asistentes:d} asistentes'
        ' y propósito "{proposito}"'
    )
)
def intentar_crear_reserva(
    sala: str,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    api_client: httpx.Client,
    context: dict,
) -> None:
    """Envía una solicitud de creación de reserva que se espera sea rechazada."""
    payload = {
        "sala": sala,
        "fecha": fecha,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "asistentes": asistentes,
        "proposito": proposito,
    }
    context["last_response"] = api_client.post("/api/v1/reservas", json=payload)


@when("se cancela la reserva")
def cancelar_reserva(api_client: httpx.Client, context: dict) -> None:
    """Envía una solicitud de cancelación de la reserva almacenada en contexto."""
    reserva_id = context["reserva_id"]
    context["last_response"] = api_client.delete(f"/api/v1/reservas/{reserva_id}")


@when(parsers.parse('se listan las reservas de la sala "{sala}"'))
def listar_reservas_sala(sala: str, api_client: httpx.Client, context: dict) -> None:
    """Consulta el listado de reservas filtrando por sala."""
    context["last_response"] = api_client.get("/api/v1/reservas", params={"sala": sala})


# ============================================================
# Then steps
# ============================================================


@then("el sistema confirma la creación de la reserva")
def confirma_creacion(context: dict) -> None:
    """Verifica la creación exitosa y que todos los campos del payload son correctos."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 201, (
        f"Se esperaba 201, se obtuvo {response.status_code}: {response.text}"
    )
    data = response.json()
    payload = context["last_payload"]
    assert data["sala"] == payload["sala"]
    assert data["fecha"] == payload["fecha"]
    assert data["hora_inicio"] == payload["hora_inicio"]
    assert data["hora_fin"] == payload["hora_fin"]
    assert data["asistentes"] == payload["asistentes"]
    assert data["proposito"] == payload["proposito"]
    assert "id" in data
    context["reserva_id"] = data["id"]


@then(parsers.parse('la reserva aparece al listar las reservas de la sala "{sala}"'))
def reserva_aparece_en_listado(sala: str, api_client: httpx.Client, context: dict) -> None:
    """Verifica que la reserva aparece en el listado filtrado por sala."""
    response = api_client.get("/api/v1/reservas", params={"sala": sala})
    assert response.status_code == 200
    reservas = response.json()
    reserva_id = context["reserva_id"]
    ids_encontrados = [r["id"] for r in reservas]
    assert reserva_id in ids_encontrados, (
        f"Reserva {reserva_id} no encontrada en listado de sala {sala}: {ids_encontrados}"
    )
    for r in reservas:
        assert r["sala"] == sala, f"Reserva de otra sala aparece en el filtro: {r}"


@then("se puede consultar la reserva por su identificador")
def consultar_reserva_por_id(api_client: httpx.Client, context: dict) -> None:
    """Verifica que la reserva es recuperable por ID con todos sus campos correctos."""
    reserva_id = context["reserva_id"]
    response = api_client.get(f"/api/v1/reservas/{reserva_id}")
    assert response.status_code == 200, (
        f"No se pudo consultar reserva {reserva_id}: {response.status_code}"
    )
    data = response.json()
    payload = context["last_payload"]
    assert data["sala"] == payload["sala"]
    assert data["fecha"] == payload["fecha"]
    assert data["hora_inicio"] == payload["hora_inicio"]
    assert data["hora_fin"] == payload["hora_fin"]
    assert data["asistentes"] == payload["asistentes"]
    assert data["proposito"] == payload["proposito"]


@then("el sistema confirma la cancelación")
def confirma_cancelacion(context: dict) -> None:
    """Verifica que la cancelación fue aceptada por el sistema."""
    response: httpx.Response = context["last_response"]
    assert response.status_code in (200, 204), (
        f"Se esperaba 200 o 204, se obtuvo {response.status_code}: {response.text}"
    )


@then(parsers.parse('la reserva ya no aparece al listar las reservas de la sala "{sala}"'))
def reserva_no_aparece_en_listado(sala: str, api_client: httpx.Client, context: dict) -> None:
    """Verifica que la reserva cancelada ya no aparece en el listado de la sala."""
    response = api_client.get("/api/v1/reservas", params={"sala": sala})
    assert response.status_code == 200
    reservas = response.json()
    reserva_id = context["reserva_id"]
    ids_encontrados = [r["id"] for r in reservas]
    assert reserva_id not in ids_encontrados, (
        f"Reserva cancelada {reserva_id} sigue apareciendo en sala {sala}"
    )


@then("el sistema rechaza la operación por horario inválido")
def rechaza_por_horario_invalido(context: dict) -> None:
    """Verifica que la reserva fue rechazada con error de validación por horario."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 422, (
        f"Se esperaba 422, se obtuvo {response.status_code}: {response.text}"
    )


@then("el sistema rechaza la operación por exceder la capacidad de la sala")
def rechaza_por_exceder_capacidad(context: dict) -> None:
    """Verifica que la reserva fue rechazada por exceder la capacidad máxima."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 422, (
        f"Se esperaba 422, se obtuvo {response.status_code}: {response.text}"
    )


@then("el sistema rechaza la operación por solapamiento de horario")
def rechaza_por_solapamiento(context: dict) -> None:
    """Verifica que la reserva fue rechazada por conflicto de horario (409)."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 409, (
        f"Se esperaba 409, se obtuvo {response.status_code}: {response.text}"
    )


@then("el sistema rechaza la operación por propósito inválido")
def rechaza_por_proposito_invalido(context: dict) -> None:
    """Verifica que la reserva fue rechazada por propósito demasiado corto."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 422, (
        f"Se esperaba 422, se obtuvo {response.status_code}: {response.text}"
    )


@then("el sistema retorna una lista vacía de reservas")
def retorna_lista_vacia(context: dict) -> None:
    """Verifica que la respuesta contiene una lista vacía."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 200, (
        f"Se esperaba 200, se obtuvo {response.status_code}: {response.text}"
    )
    assert response.json() == [], f"Se esperaba lista vacía, se obtuvo: {response.json()}"


@then("el sistema rechaza la operación por sala no reconocida")
def rechaza_por_sala_no_reconocida(context: dict) -> None:
    """Verifica que la reserva fue rechazada por usar una sala no registrada."""
    response: httpx.Response = context["last_response"]
    assert response.status_code == 422, (
        f"Se esperaba 422, se obtuvo {response.status_code}: {response.text}"
    )
