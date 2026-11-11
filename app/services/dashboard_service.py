from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.estoque import Estoque
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.ordem_servico import OrdemServico
from app.models.produto import Produto
from app.models.venda import Venda
from app.services.os_service import STATUS_ABERTOS
from app.services.venda_service import STATUS_EDITAVEIS

ZERO = Decimal("0")
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _soma(valor) -> Decimal:
    return Decimal(valor) if valor is not None else ZERO


def inicio_do_mes(data: date, deslocamento: int = 0) -> date:
    """Primeiro dia do mes de `data`, deslocado em `deslocamento` meses (negativo = passado)."""
    indice = data.year * 12 + (data.month - 1) + deslocamento
    return date(indice // 12, indice % 12 + 1, 1)


class DashboardService:
    """Indicadores do painel inicial, calculados direto no banco."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # -- vendas / operacao ------------------------------------------------------------------
    def vendas(self, hoje: date | None = None) -> dict:
        hoje = hoje or date.today()
        inicio = inicio_do_mes(hoje)
        fim = inicio_do_mes(hoje, 1)
        vendas_mes = self._faturamento_vendas(inicio, fim)
        os_mes = self._faturamento_os(inicio, fim)
        return {
            "faturamento_mes": vendas_mes[0] + os_mes[0],
            "vendas_mes": vendas_mes[1],
            "os_finalizadas_mes": os_mes[1],
            "os_abertas": self.session.scalar(
                select(func.count()).select_from(OrdemServico).where(OrdemServico.status.in_(STATUS_ABERTOS))
            ),
            "orcamentos_abertos": self.session.scalar(
                select(func.count()).select_from(Venda).where(Venda.status.in_(STATUS_EDITAVEIS))
            ),
            "serie_mensal": self.serie_mensal(hoje),
        }

    def serie_mensal(self, hoje: date | None = None, meses: int = 6) -> list[tuple[str, Decimal]]:
        """Faturamento (vendas + OS finalizadas) dos ultimos `meses` meses, do mais antigo ao atual."""
        hoje = hoje or date.today()
        serie = []
        for deslocamento in range(-(meses - 1), 1):
            inicio = inicio_do_mes(hoje, deslocamento)
            fim = inicio_do_mes(hoje, deslocamento + 1)
            total = self._faturamento_vendas(inicio, fim)[0] + self._faturamento_os(inicio, fim)[0]
            serie.append((f"{MESES[inicio.month - 1]}/{str(inicio.year)[2:]}", total))
        return serie

    def _faturamento_vendas(self, inicio: date, fim: date) -> tuple[Decimal, int]:
        inicio, fim = datetime.combine(inicio, time.min), datetime.combine(fim, time.min)
        total, quantidade = self.session.execute(
            select(func.sum(Venda.valor_total), func.count()).where(
                Venda.status == "FINALIZADA", Venda.data_venda >= inicio, Venda.data_venda < fim
            )
        ).one()
        return _soma(total), quantidade or 0

    def _faturamento_os(self, inicio: date, fim: date) -> tuple[Decimal, int]:
        # A OS nao guarda a data de finalizacao; usa-se a data de abertura como referencia do mes.
        inicio, fim = datetime.combine(inicio, time.min), datetime.combine(fim, time.min)
        total, quantidade = self.session.execute(
            select(func.sum(OrdemServico.valor_total), func.count()).where(
                OrdemServico.status == "FINALIZADA",
                OrdemServico.data_abertura >= inicio,
                OrdemServico.data_abertura < fim,
            )
        ).one()
        return _soma(total), quantidade or 0

    # -- financeiro -------------------------------------------------------------------------
    def financeiro(self, hoje: date | None = None) -> dict:
        hoje = hoje or date.today()
        proximos_7 = hoje + timedelta(days=7)

        def soma(tipo: str, *condicoes) -> Decimal:
            return _soma(
                self.session.scalar(
                    select(func.sum(FinanceiroLancamento.valor)).where(
                        FinanceiroLancamento.tipo == tipo, FinanceiroLancamento.status == "ABERTO", *condicoes
                    )
                )
            )

        entradas = _soma(self.session.scalar(select(func.sum(CaixaMovimentacao.valor)).where(CaixaMovimentacao.tipo == "ENTRADA")))
        saidas = _soma(self.session.scalar(select(func.sum(CaixaMovimentacao.valor)).where(CaixaMovimentacao.tipo == "SAIDA")))
        proximos = list(
            self.session.scalars(
                select(FinanceiroLancamento)
                .where(FinanceiroLancamento.status == "ABERTO")
                .order_by(FinanceiroLancamento.data_vencimento, FinanceiroLancamento.id)
                .limit(8)
            )
        )
        return {
            "saldo_caixa": entradas - saidas,
            "receber_vencido": soma("RECEBER", FinanceiroLancamento.data_vencimento < hoje),
            "pagar_vencido": soma("PAGAR", FinanceiroLancamento.data_vencimento < hoje),
            "receber_7_dias": soma("RECEBER", FinanceiroLancamento.data_vencimento >= hoje, FinanceiroLancamento.data_vencimento <= proximos_7),
            "pagar_7_dias": soma("PAGAR", FinanceiroLancamento.data_vencimento >= hoje, FinanceiroLancamento.data_vencimento <= proximos_7),
            "proximos_vencimentos": [
                (l.data_vencimento, l.tipo, l.descricao, l.valor, l.data_vencimento < hoje) for l in proximos
            ],
        }

    # -- estoque ----------------------------------------------------------------------------
    def estoque_baixo(self, limite: int = 10) -> list[tuple[str, str, Decimal, Decimal]]:
        """Produtos ativos com saldo menor ou igual ao minimo (produto sem saldo conta como zero)."""
        linhas = self.session.execute(
            select(Produto.codigo, Produto.descricao, func.coalesce(Estoque.quantidade_atual, 0), Produto.estoque_minimo)
            .outerjoin(Estoque, Estoque.produto_id == Produto.id)
            .where(Produto.ativo.is_(True), Produto.estoque_minimo > 0)
            .where(func.coalesce(Estoque.quantidade_atual, 0) <= Produto.estoque_minimo)
            .order_by((func.coalesce(Estoque.quantidade_atual, 0) - Produto.estoque_minimo), Produto.descricao)
            .limit(limite)
        ).all()
        return [(codigo, descricao, Decimal(atual), Decimal(minimo)) for codigo, descricao, atual, minimo in linhas]
