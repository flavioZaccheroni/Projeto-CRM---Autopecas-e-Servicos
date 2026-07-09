from datetime import date
from decimal import Decimal

from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository
from app.utils.validators import validar_obrigatorio


class FinanceiroService:
    def __init__(
        self,
        financeiro_repository: FinanceiroRepository,
        caixa_repository: CaixaMovimentacaoRepository,
    ) -> None:
        self.financeiro_repository = financeiro_repository
        self.caixa_repository = caixa_repository

    def listar_lancamentos(self) -> list[FinanceiroLancamento]:
        return self.financeiro_repository.listar()

    def listar_caixa(self) -> list[CaixaMovimentacao]:
        return self.caixa_repository.listar()

    def criar_lancamento(self, dados: dict) -> FinanceiroLancamento:
        tipo = str(dados.get("tipo") or "").strip().upper()
        if tipo not in {"RECEBER", "PAGAR"}:
            raise ValueError("Tipo deve ser RECEBER ou PAGAR.")
        validar_obrigatorio(dados.get("descricao"), "Descricao")
        valor = Decimal(str(dados.get("valor") or 0).replace(",", "."))
        if valor <= 0:
            raise ValueError("Valor deve ser maior que zero.")
        lancamento = FinanceiroLancamento(
            tipo=tipo,
            origem=dados.get("origem") or "MANUAL",
            origem_id=int(dados.get("origem_id") or 0),
            cliente_id=_id_opcional(dados.get("cliente_id")),
            fornecedor_id=_id_opcional(dados.get("fornecedor_id")),
            descricao=str(dados["descricao"]).strip(),
            valor=valor,
            data_vencimento=_parse_data(dados.get("data_vencimento")),
            status=dados.get("status") or "ABERTO",
        )
        return self.financeiro_repository.salvar(lancamento)

    def baixar_lancamento(self, lancamento_id: int, forma_pagamento: str, usuario_id: int | None = None, data_pagamento=None) -> FinanceiroLancamento:
        lancamento = self.financeiro_repository.buscar_por_id(int(lancamento_id))
        if lancamento is None:
            raise ValueError("Lancamento financeiro nao encontrado.")
        if lancamento.status == "PAGO":
            raise ValueError("Lancamento ja esta pago.")
        validar_obrigatorio(forma_pagamento, "Forma de pagamento")

        lancamento.status = "PAGO"
        lancamento.data_pagamento = _parse_data(data_pagamento)
        tipo_caixa = "ENTRADA" if lancamento.tipo == "RECEBER" else "SAIDA"
        self.caixa_repository.salvar(
            CaixaMovimentacao(
                tipo=tipo_caixa,
                descricao=lancamento.descricao,
                valor=lancamento.valor,
                forma_pagamento=str(forma_pagamento).strip(),
                usuario_id=usuario_id,
            )
        )
        return lancamento

    def estornar_lancamento(self, lancamento_id: int, usuario_id: int | None = None) -> FinanceiroLancamento:
        lancamento = self.financeiro_repository.buscar_por_id(int(lancamento_id))
        if lancamento is None:
            raise ValueError("Lancamento financeiro nao encontrado.")
        if lancamento.status != "PAGO":
            raise ValueError("Somente lancamento pago pode ser estornado.")

        lancamento.status = "ESTORNADO"
        tipo_caixa = "SAIDA" if lancamento.tipo == "RECEBER" else "ENTRADA"
        self.caixa_repository.salvar(
            CaixaMovimentacao(
                tipo=tipo_caixa,
                descricao=f"Estorno - {lancamento.descricao}",
                valor=lancamento.valor,
                forma_pagamento="ESTORNO",
                usuario_id=usuario_id,
            )
        )
        return lancamento

    def saldo_caixa(self) -> Decimal:
        saldo = Decimal("0")
        for movimento in self.caixa_repository.listar():
            valor = Decimal(movimento.valor)
            saldo += valor if movimento.tipo == "ENTRADA" else -valor
        return saldo

    def resumo_fluxo(self) -> dict[str, Decimal]:
        aberto_receber = Decimal("0")
        aberto_pagar = Decimal("0")
        pago_receber = Decimal("0")
        pago_pagar = Decimal("0")
        for lancamento in self.financeiro_repository.listar():
            valor = Decimal(lancamento.valor)
            if lancamento.status == "ABERTO" and lancamento.tipo == "RECEBER":
                aberto_receber += valor
            elif lancamento.status == "ABERTO" and lancamento.tipo == "PAGAR":
                aberto_pagar += valor
            elif lancamento.status == "PAGO" and lancamento.tipo == "RECEBER":
                pago_receber += valor
            elif lancamento.status == "PAGO" and lancamento.tipo == "PAGAR":
                pago_pagar += valor
        return {
            "aberto_receber": aberto_receber,
            "aberto_pagar": aberto_pagar,
            "pago_receber": pago_receber,
            "pago_pagar": pago_pagar,
            "saldo_caixa": self.saldo_caixa(),
        }


def _parse_data(valor) -> date:
    if isinstance(valor, date):
        return valor
    if not valor:
        return date.today()
    return date.fromisoformat(str(valor))


def _id_opcional(valor) -> int | None:
    return int(valor) if valor not in (None, "") else None
