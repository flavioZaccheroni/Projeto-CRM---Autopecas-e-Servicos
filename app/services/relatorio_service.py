from datetime import datetime
from pathlib import Path
from unicodedata import normalize

from app.config.settings import ROOT_DIR
from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.estoque import Estoque
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.ordem_servico import OrdemServico
from app.models.venda import Venda
from app.reports.exporters import export_pdf, export_xlsx
from app.repositories.base_repository import BaseRepository


class RelatorioService:
    def __init__(
        self,
        venda_repository: BaseRepository[Venda],
        estoque_repository: BaseRepository[Estoque],
        os_repository: BaseRepository[OrdemServico],
        financeiro_repository: BaseRepository[FinanceiroLancamento],
        caixa_repository: BaseRepository[CaixaMovimentacao],
        output_dir: Path | None = None,
    ) -> None:
        self.venda_repository = venda_repository
        self.estoque_repository = estoque_repository
        self.os_repository = os_repository
        self.financeiro_repository = financeiro_repository
        self.caixa_repository = caixa_repository
        self.output_dir = output_dir or ROOT_DIR / "exports" / "relatorios"

    def gerar(self, tipo: str, formato: str) -> Path:
        dataset = self.dataset(tipo)
        formato_normalizado = formato.lower()
        filename = self._filename(tipo, formato_normalizado)
        if formato_normalizado == "pdf":
            return export_pdf(filename, dataset["title"], dataset["headers"], dataset["rows"])
        if formato_normalizado == "xlsx":
            return export_xlsx(filename, dataset["title"], dataset["headers"], dataset["rows"])
        raise ValueError("Formato deve ser pdf ou xlsx.")

    def dataset(self, tipo: str) -> dict:
        tipo_normalizado = tipo.lower()
        if tipo_normalizado == "vendas":
            return {
                "title": "Relatorio de Vendas",
                "headers": ["ID", "Cliente", "Numero", "Data", "Status", "Valor"],
                "rows": [
                    [venda.id, venda.cliente_id, venda.numero, venda.data_venda, venda.status, venda.valor_total]
                    for venda in self.venda_repository.listar()
                ],
            }
        if tipo_normalizado == "estoque":
            return {
                "title": "Relatorio de Estoque",
                "headers": ["ID", "Produto", "Quantidade", "Localizacao", "Atualizado em"],
                "rows": [
                    [estoque.id, estoque.produto_id, estoque.quantidade_atual, estoque.localizacao, estoque.atualizado_em]
                    for estoque in self.estoque_repository.listar()
                ],
            }
        if tipo_normalizado == "os":
            return {
                "title": "Relatorio de Ordens de Servico",
                "headers": ["ID", "Cliente", "Veiculo", "Numero", "Abertura", "Status", "Valor"],
                "rows": [
                    [ordem.id, ordem.cliente_id, ordem.veiculo_id, ordem.numero, ordem.data_abertura, ordem.status, ordem.valor_total]
                    for ordem in self.os_repository.listar()
                ],
            }
        if tipo_normalizado == "financeiro":
            lancamentos = [
                [item.id, "Lancamento", item.tipo, item.descricao, item.valor, item.status, item.data_vencimento]
                for item in self.financeiro_repository.listar()
            ]
            caixa = [
                [item.id, "Caixa", item.tipo, item.descricao, item.valor, item.forma_pagamento, item.criado_em]
                for item in self.caixa_repository.listar()
            ]
            return {
                "title": "Relatorio Financeiro",
                "headers": ["ID", "Origem", "Tipo", "Descricao", "Valor", "Status/Forma", "Data"],
                "rows": [*lancamentos, *caixa],
            }
        raise ValueError("Tipo de relatorio deve ser vendas, estoque, os ou financeiro.")

    def _filename(self, tipo: str, formato: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = normalize("NFKD", tipo).encode("ascii", "ignore").decode("ascii").lower().replace(" ", "_")
        return self.output_dir / f"relatorio_{slug}_{timestamp}.{formato}"
