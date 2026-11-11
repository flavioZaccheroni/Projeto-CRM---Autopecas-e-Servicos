from decimal import Decimal

from app.models.item_venda import ItemVenda
from app.models.venda import Venda
from app.repositories.venda_repository import (
    FinanceiroLancamentoRepository,
    ItemVendaRepository,
    VendaRepository,
)
from app.services._itens import recalcular_total
from app.services.estoque_service import EstoqueService
from app.services.financeiro_service import cancelar_lancamentos_origem, gerar_lancamentos
from app.services.numeracao_service import NumeracaoService
from app.utils.datas import parse_data_hora
from app.utils.numeros import para_decimal
from app.utils.validators import validar_obrigatorio


# Ciclo de vida: ORCAMENTO -> APROVADO -> FINALIZADA (ou RECUSADO / CANCELADA)
STATUS_EDITAVEIS = {"ORCAMENTO", "APROVADO"}
FORMAS_PAGAMENTO = ("DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO", "BOLETO", "TRANSFERENCIA")


class VendaService:
    def __init__(
        self,
        venda_repository: VendaRepository,
        item_repository: ItemVendaRepository,
        financeiro_repository: FinanceiroLancamentoRepository,
        estoque_service: EstoqueService,
    ) -> None:
        self.venda_repository = venda_repository
        self.item_repository = item_repository
        self.financeiro_repository = financeiro_repository
        self.estoque_service = estoque_service

    @property
    def _session(self):
        return self.venda_repository.session

    def listar(self) -> list[Venda]:
        return self.venda_repository.listar()

    def criar_venda(self, dados: dict) -> Venda:
        validar_obrigatorio(dados.get("cliente_id"), "Cliente")
        numero = str(dados.get("numero") or "").strip() or NumeracaoService(self._session).proximo("VENDA")
        venda = Venda(
            cliente_id=int(dados["cliente_id"]),
            numero=numero,
            data_venda=parse_data_hora(dados.get("data_venda")),
            status=dados.get("status") or "ORCAMENTO",
            valor_total=Decimal("0"),
            usuario_id=dados.get("usuario_id"),
        )
        return self.venda_repository.salvar(venda)

    # -- itens ------------------------------------------------------------------------------
    def adicionar_item(self, venda_id: int, produto_id: int, quantidade, valor_unitario) -> ItemVenda:
        venda = self._obter_editavel(venda_id)
        quantidade_decimal = para_decimal(quantidade, "Quantidade")
        valor_unitario_decimal = para_decimal(valor_unitario, "Valor unitario")
        if quantidade_decimal <= 0 or valor_unitario_decimal < 0:
            raise ValueError("Quantidade e valor unitario invalidos.")

        item = ItemVenda(
            venda_id=venda.id,
            produto_id=int(produto_id),
            quantidade=quantidade_decimal,
            valor_unitario=valor_unitario_decimal,
            valor_total=quantidade_decimal * valor_unitario_decimal,
        )
        self.item_repository.salvar(item)
        venda.valor_total = Decimal(venda.valor_total or 0) + item.valor_total
        return item

    def atualizar_item(self, item_id: int, quantidade, valor_unitario) -> ItemVenda:
        item = self._obter_item(item_id)
        venda = self._obter_editavel(item.venda_id)
        quantidade_decimal = para_decimal(quantidade, "Quantidade")
        valor_unitario_decimal = para_decimal(valor_unitario, "Valor unitario")
        if quantidade_decimal <= 0 or valor_unitario_decimal < 0:
            raise ValueError("Quantidade e valor unitario invalidos.")
        item.quantidade = quantidade_decimal
        item.valor_unitario = valor_unitario_decimal
        item.valor_total = quantidade_decimal * valor_unitario_decimal
        self.item_repository.salvar(item)
        recalcular_total(self._session, venda)
        return item

    def remover_item(self, item_id: int) -> None:
        item = self._obter_item(item_id)
        venda = self._obter_editavel(item.venda_id)
        self.item_repository.excluir(item)
        recalcular_total(self._session, venda)

    # -- ciclo de vida ----------------------------------------------------------------------
    def aprovar_orcamento(self, venda_id: int) -> Venda:
        venda = self._obter(venda_id)
        if venda.status != "ORCAMENTO":
            raise ValueError("Somente orcamento pode ser aprovado.")
        if not venda.itens:
            raise ValueError("Orcamento precisa ter pelo menos um item para ser aprovado.")
        venda.status = "APROVADO"
        return venda

    def recusar_orcamento(self, venda_id: int, motivo: str) -> Venda:
        venda = self._obter(venda_id)
        if venda.status not in STATUS_EDITAVEIS:
            raise ValueError("Somente orcamento em aberto pode ser recusado.")
        validar_obrigatorio(motivo, "Motivo")
        venda.status = "RECUSADO"
        venda.motivo_cancelamento = motivo.strip()
        return venda

    def finalizar_venda(
        self,
        venda_id: int,
        usuario_id: int | None = None,
        data_vencimento=None,
        parcelas: int = 1,
        forma_pagamento: str | None = None,
    ) -> Venda:
        venda = self._obter(venda_id)
        if venda.status == "FINALIZADA":
            raise ValueError("Venda ja finalizada.")
        if venda.status not in STATUS_EDITAVEIS:
            raise ValueError(f"Venda {venda.status.lower()} nao pode ser finalizada.")
        if not venda.itens:
            raise ValueError("Venda precisa ter pelo menos um item para finalizacao.")
        forma = _forma_pagamento(forma_pagamento)

        for item in venda.itens:
            self.estoque_service.movimentar(
                produto_id=item.produto_id,
                tipo="SAIDA",
                quantidade=item.quantidade,
                origem=f"VENDA:{venda.numero}",
                usuario_id=usuario_id or venda.usuario_id,
            )

        venda.status = "FINALIZADA"
        venda.forma_pagamento = forma
        venda.parcelas = (1 if parcelas in (None, "") else int(parcelas))
        gerar_lancamentos(
            self.financeiro_repository,
            tipo="RECEBER",
            origem="VENDA",
            origem_id=venda.id,
            descricao=f"Venda {venda.numero}",
            valor=venda.valor_total,
            parcelas=venda.parcelas,
            primeiro_vencimento=data_vencimento,
            cliente_id=venda.cliente_id,
        )
        return venda

    def cancelar_venda(self, venda_id: int, motivo: str, usuario_id: int | None = None) -> Venda:
        venda = self._obter(venda_id)
        if venda.status == "CANCELADA":
            raise ValueError("Venda ja cancelada.")
        validar_obrigatorio(motivo, "Motivo do cancelamento")

        if venda.status == "FINALIZADA":
            for item in venda.itens:
                self.estoque_service.movimentar(
                    produto_id=item.produto_id,
                    tipo="ENTRADA",
                    quantidade=item.quantidade,
                    origem=f"CANCELAMENTO VENDA:{venda.numero}",
                    usuario_id=usuario_id or venda.usuario_id,
                )
            cancelar_lancamentos_origem(self._session, "VENDA", venda.id, usuario_id)
        venda.status = "CANCELADA"
        venda.motivo_cancelamento = motivo.strip()
        return venda

    # -- internos ---------------------------------------------------------------------------
    def _obter(self, venda_id: int) -> Venda:
        venda = self.venda_repository.buscar_por_id(int(venda_id))
        if venda is None:
            raise ValueError("Venda nao encontrada.")
        return venda

    def _obter_editavel(self, venda_id: int) -> Venda:
        venda = self._obter(venda_id)
        if venda.status not in STATUS_EDITAVEIS:
            raise ValueError(f"Venda {venda.status.lower()} nao permite alterar itens.")
        return venda

    def _obter_item(self, item_id: int) -> ItemVenda:
        item = self.item_repository.buscar_por_id(int(item_id))
        if item is None:
            raise ValueError("Item nao encontrado.")
        return item


def _forma_pagamento(valor: str | None) -> str | None:
    if not valor or not str(valor).strip():
        return None
    forma = str(valor).strip().upper()
    if forma not in FORMAS_PAGAMENTO:
        raise ValueError(f"Forma de pagamento invalida. Use: {', '.join(FORMAS_PAGAMENTO)}.")
    return forma
