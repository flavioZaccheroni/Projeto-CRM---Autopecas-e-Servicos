"""Regras compartilhadas por vendas, ordens de servico e compras (itens e pagamento)."""

from decimal import Decimal

from app.utils.numeros import para_decimal

FORMAS_PAGAMENTO = ("DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO", "BOLETO", "TRANSFERENCIA")


def validar_quantidade_valor(quantidade, valor_unitario) -> tuple[Decimal, Decimal]:
    """Converte e valida quantidade (> 0) e valor unitario (>= 0)."""
    quantidade_decimal = para_decimal(quantidade, "Quantidade")
    valor_decimal = para_decimal(valor_unitario, "Valor unitario")
    if quantidade_decimal <= 0 or valor_decimal < 0:
        raise ValueError("Quantidade e valor unitario invalidos.")
    return quantidade_decimal, valor_decimal


def normalizar_forma_pagamento(valor: str | None) -> str | None:
    if not valor or not str(valor).strip():
        return None
    forma = str(valor).strip().upper()
    if forma not in FORMAS_PAGAMENTO:
        raise ValueError(f"Forma de pagamento invalida. Use: {', '.join(FORMAS_PAGAMENTO)}.")
    return forma


def carregar_produtos(itens: list) -> list:
    """Forca o carregamento de item.produto antes de a sessao fechar (a view mostra o nome)."""
    for item in itens:
        _ = item.produto
    return itens


def recalcular_total(session, documento) -> None:
    """Recalcula valor_total somando os itens atuais (evita acumulo incremental incorreto)."""
    session.expire(documento, ["itens"])
    documento.valor_total = sum((Decimal(item.valor_total) for item in documento.itens), Decimal("0"))
