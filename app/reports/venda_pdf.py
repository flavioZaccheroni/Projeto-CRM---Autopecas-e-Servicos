"""PDF de orcamento e de venda/recibo (mesma estrutura do PDF da OS)."""

from pathlib import Path

from app.reports.exporters import export_pdf_linhas
from app.reports.os_pdf import _cabecalho, _moeda
from app.utils.datas import agora
from app.utils.logo import caminho_logo

NOMES_STATUS = {
    "ORCAMENTO": "Orcamento",
    "APROVADO": "Orcamento aprovado",
    "RECUSADO": "Orcamento recusado",
    "FINALIZADA": "Venda finalizada",
    "CANCELADA": "Venda cancelada",
}


def titulo_documento(venda) -> str:
    """Orcamento enquanto nao finalizada; 'Comprovante de venda' quando finalizada."""
    if venda.status == "FINALIZADA":
        return f"COMPROVANTE DE VENDA {venda.numero}"
    if venda.status == "CANCELADA":
        return f"VENDA {venda.numero} - CANCELADA"
    return f"ORCAMENTO {venda.numero}"


def montar_linhas_venda(venda, empresa: str | list[str] = "") -> list[str]:
    cliente = venda.cliente
    linhas = [
        *_cabecalho(empresa),
        titulo_documento(venda),
        "",
        f"Data: {venda.data_venda:%d/%m/%Y %H:%M}    Situacao: {NOMES_STATUS.get(venda.status, venda.status)}",
        f"Cliente: {cliente.nome}    Telefone: {cliente.telefone or '-'}",
        "",
        "ITENS",
        "Produto                                |  Qtd | Unitario   | Total",
        "-" * 90,
    ]
    for item in venda.itens:
        linhas.append(
            f"{item.produto.descricao[:38]:<38} | {float(item.quantidade):>4g} | "
            f"{_moeda(item.valor_unitario):>10} | {_moeda(item.valor_total):>10}"
        )
    linhas.append("-" * 90)
    if venda.desconto or venda.acrescimo:
        linhas.append(f"Subtotal: {_moeda(venda.valor_total + venda.desconto - venda.acrescimo)}")
        if venda.desconto:
            linhas.append(f"Desconto: -{_moeda(venda.desconto)}")
        if venda.acrescimo:
            linhas.append(f"Acrescimo: +{_moeda(venda.acrescimo)}")
    linhas.append(f"TOTAL: {_moeda(venda.valor_total)}")
    if venda.forma_pagamento:
        linhas.append(f"Pagamento: {venda.forma_pagamento} em {venda.parcelas}x")
    if venda.status in ("CANCELADA", "RECUSADO") and venda.motivo_cancelamento:
        linhas.append(f"Motivo: {venda.motivo_cancelamento}")
    if venda.status == "FINALIZADA":
        linhas += ["", f"Recebemos de {cliente.nome} o valor de {_moeda(venda.valor_total)} referente a esta venda."]
    elif venda.status in ("ORCAMENTO", "APROVADO"):
        linhas += ["", "Orcamento sujeito a alteracao de precos e disponibilidade de estoque."]
    linhas += [
        "",
        "",
        "_______________________________        _______________________________",
        "Assinatura do cliente                  Responsavel",
        "",
        f"Impresso em {agora():%d/%m/%Y %H:%M}",
    ]
    return linhas


def gerar_pdf_venda(venda, pasta: Path, empresa: str | list[str] = "") -> Path:
    prefixo = "venda" if venda.status == "FINALIZADA" else "orcamento"
    destino = pasta / f"{prefixo}_{venda.numero}_{agora():%Y%m%d_%H%M%S}.pdf"
    return export_pdf_linhas(destino, montar_linhas_venda(venda, empresa), logo=caminho_logo())
