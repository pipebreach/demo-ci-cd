"""Business logic and in-memory storage."""

from datetime import date
from typing import TypedDict
from uuid import uuid4

from src.models import ReservaCreate, ReservaResponse, SalaResponse

SALAS: dict[str, int] = {"A": 4, "B": 8, "C": 20}
HORA_INICIO_LABORAL = "08:00"
HORA_FIN_LABORAL = "20:00"
DURACION_MINIMA_MIN = 15
DURACION_MAXIMA_MIN = 240

_ERR_HORA_FIN_INVALIDA = "La hora de fin debe ser posterior a la hora de inicio"
_ERR_SOLAPAMIENTO = "Existe un solapamiento de horario con otra reserva"
_ERR_RESERVA_NO_ENCONTRADA = "Reserva '{}' no encontrada"
_ERR_RESERVA_PASADA = "Solo se pueden cancelar reservas futuras"


class ConflictoError(ValueError):
    """Error de conflicto de estado en la reserva."""


class _ReservaDato(TypedDict):
    id: str
    sala: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    asistentes: int
    proposito: str


_storage: dict[str, _ReservaDato] = {}


def _hora_a_minutos(hora: str) -> int:
    """Convierte una hora en formato HH:MM a minutos desde medianoche."""
    hh, mm = hora.split(":")
    return int(hh) * 60 + int(mm)


def _dato_a_response(dato: _ReservaDato) -> ReservaResponse:
    """Convierte un _ReservaDato a ReservaResponse."""
    return ReservaResponse(**dato)


def crear_reserva(data: ReservaCreate) -> ReservaResponse:
    """Crea una nueva reserva de sala."""
    if data.sala not in SALAS:
        raise ValueError(f"Sala '{data.sala}' no reconocida")

    inicio_min = _hora_a_minutos(data.hora_inicio)
    fin_min = _hora_a_minutos(data.hora_fin)
    laboral_inicio = _hora_a_minutos(HORA_INICIO_LABORAL)
    laboral_fin = _hora_a_minutos(HORA_FIN_LABORAL)

    if fin_min <= inicio_min:
        raise ValueError(_ERR_HORA_FIN_INVALIDA)

    duracion = fin_min - inicio_min
    if duracion < DURACION_MINIMA_MIN:
        raise ValueError(f"La duración mínima de la reserva es {DURACION_MINIMA_MIN} minutos")
    if duracion > DURACION_MAXIMA_MIN:
        raise ValueError(f"La duración máxima de la reserva es {DURACION_MAXIMA_MIN // 60} horas")

    if inicio_min < laboral_inicio or fin_min > laboral_fin:
        raise ValueError(
            f"El horario debe estar dentro del horario laboral "
            f"({HORA_INICIO_LABORAL}-{HORA_FIN_LABORAL})"
        )

    if data.asistentes > SALAS[data.sala]:
        raise ValueError(
            f"La sala '{data.sala}' tiene capacidad máxima de {SALAS[data.sala]} asistentes"
        )

    for reserva in _storage.values():
        if reserva["sala"] == data.sala and reserva["fecha"] == data.fecha:
            r_inicio = _hora_a_minutos(reserva["hora_inicio"])
            r_fin = _hora_a_minutos(reserva["hora_fin"])
            if inicio_min < r_fin and fin_min > r_inicio:
                raise ConflictoError(_ERR_SOLAPAMIENTO)

    reserva_id = str(uuid4())
    dato: _ReservaDato = {
        "id": reserva_id,
        "sala": data.sala,
        "fecha": data.fecha,
        "hora_inicio": data.hora_inicio,
        "hora_fin": data.hora_fin,
        "asistentes": data.asistentes,
        "proposito": data.proposito,
    }
    _storage[reserva_id] = dato
    return _dato_a_response(dato)


def listar_salas() -> list[SalaResponse]:
    """Devuelve la lista de salas con sus capacidades máximas."""
    return [
        SalaResponse(sala=sala, capacidad=capacidad) for sala, capacidad in sorted(SALAS.items())
    ]


def listar_reservas(sala: str | None = None) -> list[ReservaResponse]:
    """Lista todas las reservas, opcionalmente filtradas por sala."""
    reservas = list(_storage.values())
    if sala is not None:
        reservas = [r for r in reservas if r["sala"] == sala]
    return [_dato_a_response(r) for r in reservas]


def obtener_reserva(reserva_id: str) -> ReservaResponse:
    """Obtiene una reserva por su ID."""
    if reserva_id not in _storage:
        raise KeyError(_ERR_RESERVA_NO_ENCONTRADA.format(reserva_id))
    return _dato_a_response(_storage[reserva_id])


def cancelar_reserva(reserva_id: str) -> None:
    """Cancela una reserva futura."""
    if reserva_id not in _storage:
        raise KeyError(_ERR_RESERVA_NO_ENCONTRADA.format(reserva_id))

    reserva = _storage[reserva_id]
    fecha_reserva = date.fromisoformat(reserva["fecha"])
    if fecha_reserva <= date.today():
        raise ConflictoError(_ERR_RESERVA_PASADA)

    del _storage[reserva_id]


def _reset() -> None:
    """Limpia el almacenamiento en memoria (para tests)."""
    _storage.clear()
