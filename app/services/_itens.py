from decimal import Decimal


def recalcular_total(session, documento) -> None:
    """Recalcula valor_total somando os itens atuais (evita acumulo incremental incorreto)."""
    session.expire(documento, ["itens"])
    documento.valor_total = sum((Decimal(item.valor_total) for item in documento.itens), Decimal("0"))
