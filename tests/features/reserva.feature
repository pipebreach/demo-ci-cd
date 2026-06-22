# language: es

Característica: Reserva de salas de reunión

  Como empleado de la empresa
  Quiero reservar salas de reunión disponibles
  Para organizar reuniones respetando capacidades y horarios

  Antecedentes:
    Dado que el sistema gestiona las siguientes salas con sus capacidades máximas:
      | sala | capacidad |
      | A    | 4         |
      | B    | 8         |
      | C    | 20        |
    Y que el horario laboral permitido para reservas es de "08:00" a "20:00"

  Escenario: Flujo principal - Crear una reserva válida y listarla por sala
    Dado que no existen reservas para la sala "B"
    Cuando se crea una reserva para la sala "B" el día "2099-06-01" de "10:00" a "11:00" con 5 asistentes y propósito "Revisión semanal del equipo de plataforma"
    Entonces el sistema confirma la creación de la reserva
    Y la reserva aparece al listar las reservas de la sala "B"
    Y se puede consultar la reserva por su identificador

  Escenario: Flujo principal - Cancelar una reserva futura
    Dado que existe una reserva para la sala "A" el día "2099-07-01" de "09:00" a "09:30" con 3 asistentes y propósito "Revisión de diseño del sprint"
    Cuando se cancela la reserva
    Entonces el sistema confirma la cancelación
    Y la reserva ya no aparece al listar las reservas de la sala "A"

  Esquema del escenario: Validación - Rechazar reserva con horario inválido
    Cuando se intenta crear una reserva para la sala "B" el día "2099-06-01" de "<hora_inicio>" a "<hora_fin>" con 5 asistentes y propósito "Revisión semanal del equipo de plataforma"
    Entonces el sistema rechaza la operación por horario inválido

    Ejemplos:
      | hora_inicio | hora_fin |
      | 11:00       | 10:00    |
      | 10:00       | 10:10    |
      | 10:00       | 14:01    |
      | 07:00       | 08:00    |

  Escenario: Validación - Rechazar reserva que excede la capacidad de la sala
    Cuando se intenta crear una reserva para la sala "A" el día "2099-06-01" de "10:00" a "11:00" con 10 asistentes y propósito "Revisión semanal del equipo de plataforma"
    Entonces el sistema rechaza la operación por exceder la capacidad de la sala

  Escenario: Validación - Rechazar reserva con solapamiento de horario
    Dado que existe una reserva para la sala "B" el día "2099-06-01" de "10:00" a "11:00" con 5 asistentes y propósito "Revisión semanal del equipo de plataforma"
    Cuando se intenta crear una reserva para la sala "B" el día "2099-06-01" de "10:30" a "11:30" con 4 asistentes y propósito "Seguimiento del proyecto de migración"
    Entonces el sistema rechaza la operación por solapamiento de horario

  Escenario: Validación - Rechazar reserva con propósito inválido
    Cuando se intenta crear una reserva para la sala "B" el día "2099-06-01" de "10:00" a "11:00" con 5 asistentes y propósito "Breve"
    Entonces el sistema rechaza la operación por propósito inválido

  Escenario: Caso límite - Listar las reservas de una sala sin reservas registradas
    Dado que no existen reservas para la sala "C"
    Cuando se listan las reservas de la sala "C"
    Entonces el sistema retorna una lista vacía de reservas

  Escenario: Seguridad - Rechazar reserva para una sala no reconocida
    Cuando se intenta crear una reserva para la sala "Z" el día "2099-06-01" de "10:00" a "11:00" con 5 asistentes y propósito "Reunión de revisión del proyecto de infraestructura"
    Entonces el sistema rechaza la operación por sala no reconocida
