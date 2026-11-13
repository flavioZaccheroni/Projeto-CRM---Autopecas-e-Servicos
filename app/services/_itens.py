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


CENTAVOS = Decimal("0.01")
CHAVE_DESCONTO_MAX = "desconto.max_percentual"  # limite (%) para quem nao e administrador
PADRAO_DESCONTO_MAX = Decimal("10")


def subtotal_itens(documento) -> Decimal:
    return sum((Decimal(item.valor_total) for item in documento.itens), Decimal("0"))


def interpretar_ajuste(valor, base: Decimal, campo: str = "Valor") -> Decimal:
    """Aceita 'R$' (12,50) ou percentual ('10%') sobre a base. Vazio = 0. Nunca negativo."""
    texto = "" if valor is None else str(valor).strip()
    if not texto:
        return Decimal("0")
    if texto.endswith("%"):
        percentual = para_decimal(texto[:-1], campo)
        if percentual < 0 or percentual > 100:
            raise ValueError(f"{campo}: percentual deve ficar entre 0% e 100%.")
        return (base * percentual / 100).quantize(CENTAVOS)
    numero = para_decimal(texto.replace("R$", ""), campo)
    if numero < 0:
        raise ValueError(f"{campo} nao pode ser negativo.")
    return numero.quantize(CENTAVOS)


def recalcular_total(session, documento) -> None:
    """Recalcula valor_total = itens - desconto + acrescimo (compras nao tem ajuste).

    O desconto nunca passa do subtotal: ao remover itens ele e reduzido para o total nao ficar negativo.
    """
    session.expire(documento, ["itens"])
    subtotal = subtotal_itens(documento)
    desconto = Decimal(getattr(documento, "desconto", 0) or 0)
    acrescimo = Decimal(getattr(documento, "acrescimo", 0) or 0)
    if hasattr(documento, "desconto") and desconto > subtotal:
        desconto = documento.desconto = subtotal
    documento.valor_total = subtotal - desconto + acrescimo


def definir_ajuste(session, documento, desconto, acrescimo, limite_percentual: Decimal | None = None) -> Decimal:
    """Define desconto e acrescimo do documento (valor ou %), valida o limite e recalcula o total.

    `limite_percentual` None = sem limite (administrador). Devolve o percentual de desconto aplicado.
    """
    session.expire(documento, ["itens"])
    subtotal = subtotal_itens(documento)
    valor_desc = interpretar_ajuste(desconto, subtotal, "Desconto")
    valor_acre = interpretar_ajuste(acrescimo, subtotal, "Acrescimo")
    if valor_desc > subtotal:
        raise ValueError("O desconto nao pode ser maior que o total dos itens.")
    percentual = (valor_desc * 100 / subtotal) if subtotal > 0 else Decimal("0")
    if limite_percentual is not None and percentual > limite_percentual:
        raise ValueError(
            f"Desconto de {percentual:.1f}% acima do limite do seu perfil ({limite_percentual:.1f}%). "
            "Peca a um administrador."
        )
    documento.desconto = valor_desc
    documento.acrescimo = valor_acre
    recalcular_total(session, documento)
    return percentual
