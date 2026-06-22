"""FastAPI application with endpoints."""

from fastapi import FastAPI, HTTPException

from src.models import ReservaCreate, ReservaResponse, SalaResponse
from src.services import ConflictoError, _reset
from src.services import cancelar_reserva as cancelar_reserva_service
from src.services import crear_reserva as crear_reserva_service
from src.services import listar_reservas as listar_reservas_service
from src.services import listar_salas as listar_salas_service
from src.services import obtener_reserva as obtener_reserva_service

app = FastAPI(
    title="DevSecOps Agentic Demo",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/salas", response_model=list[SalaResponse])
def listar_salas() -> list[SalaResponse]:
    """Lista las salas disponibles con sus capacidades máximas."""
    return listar_salas_service()


@app.post("/api/v1/reservas", response_model=ReservaResponse, status_code=201)
def crear_reserva(data: ReservaCreate) -> ReservaResponse:
    """Crea una nueva reserva de sala."""
    try:
        return crear_reserva_service(data)
    except ConflictoError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/v1/reservas", response_model=list[ReservaResponse])
def listar_reservas(sala: str | None = None) -> list[ReservaResponse]:
    """Lista reservas, opcionalmente filtradas por sala."""
    return listar_reservas_service(sala)


@app.get("/api/v1/reservas/{reserva_id}", response_model=ReservaResponse)
def obtener_reserva(reserva_id: str) -> ReservaResponse:
    """Obtiene una reserva por su ID."""
    try:
        return obtener_reserva_service(reserva_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=e.args[0])


@app.delete("/api/v1/reservas/{reserva_id}", status_code=204)
def cancelar_reserva(reserva_id: str) -> None:
    """Cancela una reserva futura."""
    try:
        cancelar_reserva_service(reserva_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    except ConflictoError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/api/v1/_reset", status_code=204)
def reset_estado() -> None:
    """Limpia el estado en memoria. Solo para testing."""
    _reset()
