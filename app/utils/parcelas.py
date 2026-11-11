from datetime import date
from decimal import ROUND_DOWN, Decimal

from app.utils.datas import somar_dias


def gerar_parcelas(
    valor: Decimal,
    quantidade: int,
    primeiro_vencimento: date,
    intervalo_dias: int = 30,
) -> list[tuple[Decimal, date]]:
    """Divide `valor` em `quantidade` parcelas; o resto de arredondamento vai na ultima."""
    quantidade = 1 if quantidade in (None, "") else int(quantidade)
    if quantidade < 1 or quantidade > 60:
        raise ValueError("Numero de parcelas deve estar entre 1 e 60.")
    valor = Decimal(valor)
    base = (valor / quantidade).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    parcelas: list[tuple[Decimal, date]] = []
    acumulado = Decimal("0")
    for numero in range(quantidade):
        parcela = base if numero < quantidade - 1 else valor - acumulado
        acumulado += parcela
        parcelas.append((parcela, somar_dias(primeiro_vencimento, intervalo_dias * numero)))
    return parcelas
