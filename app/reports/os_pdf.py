from pathlib import Path

from app.reports.exporters import export_pdf_linhas
from app.utils.datas import agora


def _moeda(valor) -> str:
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_linhas_os(ordem, empresa: str = "") -> list[str]:
    """Texto da ordem de servico pronto para impressao (cabecalho, cliente, itens, totais, assinaturas)."""
    veiculo = ordem.veiculo
    linhas = [
        empresa or "ERP CRM Autopecas & Servicos",
        f"ORDEM DE SERVICO {ordem.numero}",
        "",
        f"Data de abertura: {ordem.data_abertura:%d/%m/%Y %H:%M}    Status: {ordem.status}",
        f"Cliente: {ordem.cliente.nome}    Telefone: {ordem.cliente.telefone or '-'}",
        f"Veiculo: {veiculo.placa} - {veiculo.marca or ''} {veiculo.modelo or ''}  Ano: {veiculo.ano or '-'}  KM: {veiculo.km_atual or '-'}",
        "",
        f"Defeito relatado: {ordem.defeito_relatado or '-'}",
        f"Diagnostico: {ordem.diagnostico or '-'}",
        "",
        "ITENS",
        "Tipo    | Descricao                          |  Qtd | Unitario   | Total",
        "-" * 90,
    ]
    for item in ordem.itens:
        linhas.append(
            f"{item.tipo:<7} | {item.descricao[:34]:<34} | {float(item.quantidade):>4g} | "
            f"{_moeda(item.valor_unitario):>10} | {_moeda(item.valor_total):>10}"
        )
    linhas += [
        "-" * 90,
        f"TOTAL: {_moeda(ordem.valor_total)}",
    ]
    if ordem.forma_pagamento:
        linhas.append(f"Pagamento: {ordem.forma_pagamento} em {ordem.parcelas}x")
    if ordem.status == "CANCELADA" and ordem.motivo_cancelamento:
        linhas.append(f"CANCELADA - Motivo: {ordem.motivo_cancelamento}")
    linhas += [
        "",
        "",
        "_______________________________        _______________________________",
        "Assinatura do cliente                  Responsavel pela oficina",
        "",
        f"Impresso em {agora():%d/%m/%Y %H:%M}",
    ]
    return linhas


def gerar_pdf_os(ordem, pasta: Path, empresa: str = "") -> Path:
    destino = pasta / f"os_{ordem.numero}_{agora():%Y%m%d_%H%M%S}.pdf"
    return export_pdf_linhas(destino, montar_linhas_os(ordem, empresa))
