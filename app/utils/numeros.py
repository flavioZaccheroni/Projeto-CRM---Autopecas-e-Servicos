from decimal import Decimal, InvalidOperation


def para_decimal(valor, campo: str = "Valor") -> Decimal:
    """Converte texto/numero (aceita virgula decimal) para Decimal, com erro amigavel."""
    try:
        return Decimal(str(valor).strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise ValueError(f"{campo} numerico invalido.") from None
