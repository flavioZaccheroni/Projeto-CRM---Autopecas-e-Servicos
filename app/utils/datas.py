from datetime import date, datetime, timedelta, timezone


def agora() -> datetime:
    """Data/hora atual em UTC, sem tzinfo (compativel com as colunas DateTime do SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_data(valor) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if not valor:
        return date.today()
    return date.fromisoformat(str(valor).strip())


def parse_data_hora(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if not valor:
        return agora()
    return datetime.fromisoformat(str(valor).strip())


def somar_dias(data: date, dias: int) -> date:
    return data + timedelta(days=dias)
