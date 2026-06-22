"""Step definitions para el dominio de reservas de salas."""

from collections.abc import Generator

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.services import HORA_FIN_LABORAL, HORA_INICIO_LABORAL, SALAS, _reset

scenarios("../features/reserva.feature")


@pytest.fixture
def context() -> dict:
    """Contexto compartido entre steps del escenario."""
    return {}


@pytest.fixture(autouse=True)
def _limpia_estado() -> Generator[None, None, None]:
    """Limpia el estado en memoria antes y después de cada test."""
    _reset()
    yield
    _reset()


# ── Antecedentes ──────────────────────────────────────────────────────────────


@given("que el sistema gestiona las siguientes salas con sus capacidades máximas:")
def gestionar_salas(datatable: list[list[str]]) -> None:
    """Verifica que el sistema gestiona las salas y capacidades correctas."""
    assert datatable[0] == ["sala", "capacidad"]
    for fila in datatable[1:]:
        assert fila[0] in SALAS, f"Sala inesperada: {fila[0]}"
        assert int(fila[1]) == SALAS[fila[0]], f"Capacidad incorrecta para sala {fila[0]}"


@given(
    parsers.parse(
        'que el horario laboral permitido para reservas es de "{hora_inicio}" a "{hora_fin}"'
    )
)
def verificar_horario_laboral(hora_inicio: str, hora_fin: str) -> None:
    """Verifica que el horario laboral configurado sea el correcto."""
    assert hora_inicio == HORA_INICIO_LABORAL
    assert hora_fin == HORA_FIN_LABORAL


# ── Dados ─────────────────────────────────────────────────────────────────────


@given(parsers.parse('que no existen reservas para la sala "{sala}"'))
def no_existen_reservas(sala: str, client) -> None:
    """Verifica que no hay reservas para la sala indicada."""
    response = client.get(f"/api/v1/reservas?sala={sala}")
    assert response.status_code == 200
    assert response.json() == []


@given(
    parsers.parse(
        'que existe una reserva para la sala "{sala}" el día "{fecha}" de "{hora_inicio}" a '
        '"{hora_fin}" con {asistentes:d} asistentes y propósito "{proposito}"'
    )
)
def existe_reserva(
    sala: str,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    client,
    context: dict,
) -> None:
    """Crea una reserva como precondición del escenario."""
    response = client.post(
        "/api/v1/reservas",
        json={
            "sala": sala,
            "fecha": fecha,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "asistentes": asistentes,
            "proposito": proposito,
        },
    )
    assert response.status_code == 201
    context["reserva"] = response.json()


# ── Cuandos ───────────────────────────────────────────────────────────────────


@when(
    parsers.parse(
        'se crea una reserva para la sala "{sala}" el día "{fecha}" de "{hora_inicio}" a '
        '"{hora_fin}" con {asistentes:d} asistentes y propósito "{proposito}"'
    )
)
def crear_reserva(
    sala: str,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    client,
    context: dict,
) -> None:
    """Crea una reserva de sala."""
    response = client.post(
        "/api/v1/reservas",
        json={
            "sala": sala,
            "fecha": fecha,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "asistentes": asistentes,
            "proposito": proposito,
        },
    )
    context["response"] = response


@when(
    parsers.parse(
        'se intenta crear una reserva para la sala "{sala}" el día "{fecha}" de "{hora_inicio}" a '
        '"{hora_fin}" con {asistentes:d} asistentes y propósito "{proposito}"'
    )
)
def intentar_crear_reserva(
    sala: str,
    fecha: str,
    hora_inicio: str,
    hora_fin: str,
    asistentes: int,
    proposito: str,
    client,
    context: dict,
) -> None:
    """Intenta crear una reserva (puede ser rechazada)."""
    response = client.post(
        "/api/v1/reservas",
        json={
            "sala": sala,
            "fecha": fecha,
            "hora_inicio": hora_inicio,
            "hora_fin": hora_fin,
            "asistentes": asistentes,
            "proposito": proposito,
        },
    )
    context["response"] = response


@when("se cancela la reserva")
def cancelar_reserva(client, context: dict) -> None:
    """Cancela la reserva creada como precondición."""
    reserva_id = context["reserva"]["id"]
    response = client.delete(f"/api/v1/reservas/{reserva_id}")
    context["response"] = response


@when(parsers.parse('se listan las reservas de la sala "{sala}"'))
def listar_reservas_sala(sala: str, client, context: dict) -> None:
    """Lista las reservas de una sala."""
    response = client.get(f"/api/v1/reservas?sala={sala}")
    context["response"] = response


# ── Entonces ──────────────────────────────────────────────────────────────────


@then("el sistema confirma la creación de la reserva")
def confirmar_creacion(context: dict) -> None:
    """Verifica que la reserva fue creada exitosamente."""
    assert context["response"].status_code == 201
    data = context["response"].json()
    assert "id" in data
    context["reserva"] = data


@then("el sistema confirma la cancelación")
def confirmar_cancelacion(context: dict) -> None:
    """Verifica que la reserva fue cancelada exitosamente."""
    assert context["response"].status_code == 204


@then(parsers.parse('la reserva aparece al listar las reservas de la sala "{sala}"'))
def reserva_en_lista(sala: str, client, context: dict) -> None:
    """Verifica que la reserva aparece en la lista de la sala."""
    response = client.get(f"/api/v1/reservas?sala={sala}")
    assert response.status_code == 200
    reservas = response.json()
    ids = [r["id"] for r in reservas]
    assert context["reserva"]["id"] in ids


@then("se puede consultar la reserva por su identificador")
def consultar_por_id(client, context: dict) -> None:
    """Verifica que la reserva puede consultarse por su ID y contiene todos los campos."""
    reserva_id = context["reserva"]["id"]
    response = client.get(f"/api/v1/reservas/{reserva_id}")
    assert response.status_code == 200
    data = response.json()
    for campo in ("sala", "fecha", "hora_inicio", "hora_fin", "asistentes", "proposito"):
        assert data[campo] == context["reserva"][campo]


@then(parsers.parse('la reserva ya no aparece al listar las reservas de la sala "{sala}"'))
def reserva_no_en_lista(sala: str, client, context: dict) -> None:
    """Verifica que la reserva no aparece en la lista de la sala tras cancelarla."""
    response = client.get(f"/api/v1/reservas?sala={sala}")
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()]
    assert context["reserva"]["id"] not in ids


@then("el sistema retorna una lista vacía de reservas")
def lista_vacia(context: dict) -> None:
    """Verifica que la respuesta es una lista vacía."""
    assert context["response"].status_code == 200
    assert context["response"].json() == []


@then("el sistema rechaza la operación por horario inválido")
def rechazar_horario_invalido(context: dict) -> None:
    """Verifica que la operación fue rechazada por horario inválido."""
    assert 400 <= context["response"].status_code < 500


@then("el sistema rechaza la operación por exceder la capacidad de la sala")
def rechazar_capacidad_excedida(context: dict) -> None:
    """Verifica que la operación fue rechazada por exceder la capacidad."""
    assert 400 <= context["response"].status_code < 500


@then("el sistema rechaza la operación por solapamiento de horario")
def rechazar_solapamiento(context: dict) -> None:
    """Verifica que la operación fue rechazada por solapamiento de horario."""
    assert context["response"].status_code == 409


@then("el sistema rechaza la operación por propósito inválido")
def rechazar_proposito_invalido(context: dict) -> None:
    """Verifica que la operación fue rechazada por propósito inválido."""
    assert 400 <= context["response"].status_code < 500


@then("el sistema rechaza la operación por sala no reconocida")
def rechazar_sala_no_reconocida(context: dict) -> None:
    """Verifica que la operación fue rechazada por sala no reconocida."""
    assert 400 <= context["response"].status_code < 500
