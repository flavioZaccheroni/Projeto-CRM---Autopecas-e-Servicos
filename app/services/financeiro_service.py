from decimal import Decimal

from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository
from app.utils.datas import parse_data
from app.utils.parcelas import gerar_parcelas
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
            data_vencimento=parse_data(dados.get("data_vencimento")),
            status=dados.get("status") or "ABERTO",
        )
        return self.financeiro_repository.salvar(lancamento)

    def baixar_lancamento(self, lancamento_id: int, forma_pagamento: str, usuario_id: int | None = None, data_pagamento=None) -> FinanceiroLancamento:
        lancamento = self.financeiro_repository.buscar_por_id(int(lancamento_id))
        if lancamento is None:
            raise ValueError("Lancamento financeiro nao encontrado.")
        if lancamento.status == "PAGO":
            raise ValueError("Lancamento ja esta pago.")
        if lancamento.status != "ABERTO":
            raise ValueError(f"Lancamento {lancamento.status.lower()} nao pode ser baixado.")
        validar_obrigatorio(forma_pagamento, "Forma de pagamento")

        lancamento.status = "PAGO"
        lancamento.data_pagamento = parse_data(data_pagamento)
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


def _id_opcional(valor) -> int | None:
    return int(valor) if valor not in (None, "") else None


def gerar_lancamentos(
    repository: FinanceiroRepository,
    tipo: str,
    origem: str,
    origem_id: int,
    descricao: str,
    valor: Decimal,
    parcelas: int = 1,
    primeiro_vencimento=None,
    cliente_id: int | None = None,
    fornecedor_id: int | None = None,
) -> list[FinanceiroLancamento]:
    """Cria 1..N lancamentos (parcelas) para um documento de origem (venda, OS ou compra)."""
    vencimento = parse_data(primeiro_vencimento)
    divisao = gerar_parcelas(Decimal(valor), parcelas, vencimento)
    criados = []
    for numero, (valor_parcela, data) in enumerate(divisao, start=1):
        sufixo = f" ({numero}/{len(divisao)})" if len(divisao) > 1 else ""
        criados.append(
            repository.salvar(
                FinanceiroLancamento(
                    tipo=tipo,
                    origem=origem,
                    origem_id=origem_id,
                    cliente_id=cliente_id,
                    fornecedor_id=fornecedor_id,
                    descricao=f"{descricao}{sufixo}",
                    valor=valor_parcela,
                    data_vencimento=data,
                    status="ABERTO",
                )
            )
        )
    return criados


def cancelar_lancamentos_origem(session, origem: str, origem_id: int, usuario_id: int | None = None) -> int:
    """Cancela os lancamentos em aberto de um documento e estorna os ja pagos (movimentando o caixa)."""
    from sqlalchemy import select

    servico = FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session))
    lancamentos = list(
        session.scalars(
            select(FinanceiroLancamento).where(
                FinanceiroLancamento.origem == origem, FinanceiroLancamento.origem_id == origem_id
            )
        )
    )
    afetados = 0
    for lancamento in lancamentos:
        if lancamento.status == "ABERTO":
            lancamento.status = "CANCELADO"
            afetados += 1
        elif lancamento.status == "PAGO":
            servico.estornar_lancamento(lancamento.id, usuario_id)
            afetados += 1
    session.flush()
    return afetados
