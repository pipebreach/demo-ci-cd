"""Pydantic models for the application."""

from pydantic import BaseModel, Field


class ReservaCreate(BaseModel):
    """Datos para crear una reserva de sala."""

    sala: str = Field(..., min_length=1, max_length=10)
    fecha: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    hora_inicio: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    hora_fin: str = Field(..., pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    asistentes: int = Field(..., ge=1)
    proposito: str = Field(..., min_length=10, max_length=500)


class ReservaResponse(BaseModel):
    """Reserva con ID asignado."""

    id: str
    sala: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    asistentes: int
    proposito: str


class SalaResponse(BaseModel):
    """Sala de reunión con su capacidad máxima."""

    sala: str = Field(..., min_length=1, max_length=10)
    capacidad: int = Field(..., ge=1)
