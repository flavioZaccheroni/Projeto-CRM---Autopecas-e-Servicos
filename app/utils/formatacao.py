"""Formatacao de valores para exibicao (independente de toolkit de interface)."""

from datetime import date, datetime
from decimal import Decimal


def format_value(value) -> str:
    """Formata para exibicao: datas dd/mm/aaaa, valores no padrao brasileiro, booleanos como Sim/Nao."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Nao"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, Decimal):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)
