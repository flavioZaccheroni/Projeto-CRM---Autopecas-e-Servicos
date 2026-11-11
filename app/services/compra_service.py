from decimal import Decimal

from app.models.compra import Compra
from app.models.item_compra import ItemCompra
from app.repositories.compra_repository import CompraRepository, ItemCompraRepository
from app.services._itens import (
    carregar_produtos,
    recalcular_total,
    validar_quantidade_valor,
)
from app.services.estoque_service import EstoqueService
from app.services.financeiro_service import cancelar_lancamentos_origem, gerar_lancamentos
from app.services.numeracao_service import NumeracaoService
from app.utils.datas import parse_data
from app.utils.validators import validar_obrigatorio


class CompraService:
    def __init__(
        self,
        compra_repository: CompraRepository,
        item_repository: ItemCompraRepository,
        estoque_service: EstoqueService,
        financeiro_repository=None,
    ) -> None:
        self.compra_repository = compra_repository
        self.item_repository = item_repository
        self.estoque_service = estoque_service
        self.financeiro_repository = financeiro_repository

    @property
    def _session(self):
        return self.compra_repository.session

    def listar(self) -> list[Compra]:
        return self.compra_repository.listar()

    def criar_compra(self, dados: dict) -> Compra:
        validar_obrigatorio(dados.get("fornecedor_id"), "Fornecedor")
        numero = str(dados.get("numero") or "").strip() or NumeracaoService(self._session).proximo("COMPRA")
        compra = Compra(
            fornecedor_id=int(dados["fornecedor_id"]),
            numero=numero,
            data_compra=parse_data(dados.get("data_compra")),
            status=dados.get("status") or "ABERTA",
            valor_total=Decimal("0"),
            usuario_id=dados.get("usuario_id"),
        )
        return self.compra_repository.salvar(compra)

    # -- itens ------------------------------------------------------------------------------
    def adicionar_item(self, compra_id: int, produto_id: int, quantidade, valor_unitario) -> ItemCompra:
        compra = self._obter_editavel(compra_id)
        quantidade_decimal, valor_unitario_decimal = validar_quantidade_valor(quantidade, valor_unitario)

        item = ItemCompra(
            compra_id=compra.id,
            produto_id=int(produto_id),
            quantidade=quantidade_decimal,
            valor_unitario=valor_unitario_decimal,
            valor_total=quantidade_decimal * valor_unitario_decimal,
        )
        self.item_repository.salvar(item)
        compra.valor_total = Decimal(compra.valor_total or 0) + item.valor_total
        return item

    def atualizar_item(self, item_id: int, quantidade, valor_unitario) -> ItemCompra:
        item = self._obter_item(item_id)
        compra = self._obter_editavel(item.compra_id)
        quantidade_decimal, valor_unitario_decimal = validar_quantidade_valor(quantidade, valor_unitario)
        item.quantidade = quantidade_decimal
        item.valor_unitario = valor_unitario_decimal
        item.valor_total = quantidade_decimal * valor_unitario_decimal
        self.item_repository.salvar(item)
        recalcular_total(self._session, compra)
        return item

    def remover_item(self, item_id: int) -> None:
        item = self._obter_item(item_id)
        compra = self._obter_editavel(item.compra_id)
        self.item_repository.excluir(item)
        recalcular_total(self._session, compra)

    def listar_itens(self, documento_id: int) -> list:
        return carregar_produtos(list(self._obter(documento_id).itens))

    # -- ciclo de vida ----------------------------------------------------------------------
    def receber_compra(
        self,
        compra_id: int,
        usuario_id: int | None = None,
        data_vencimento=None,
        parcelas: int = 1,
    ) -> Compra:
        compra = self._obter(compra_id)
        if compra.status == "RECEBIDA":
            raise ValueError("Compra ja recebida.")
        if compra.status != "ABERTA":
            raise ValueError(f"Compra {compra.status.lower()} nao pode ser recebida.")
        if not compra.itens:
            raise ValueError("Compra precisa ter pelo menos um item para recebimento.")

        for item in compra.itens:
            self.estoque_service.movimentar(
                produto_id=item.produto_id,
                tipo="ENTRADA",
                quantidade=item.quantidade,
                origem=f"COMPRA:{compra.numero}",
                usuario_id=usuario_id or compra.usuario_id,
            )
        compra.status = "RECEBIDA"
        if self.financeiro_repository is not None:
            gerar_lancamentos(
                self.financeiro_repository,
                tipo="PAGAR",
                origem="COMPRA",
                origem_id=compra.id,
                descricao=f"Compra {compra.numero}",
                valor=compra.valor_total,
                parcelas=parcelas,
                primeiro_vencimento=data_vencimento,
                fornecedor_id=compra.fornecedor_id,
            )
        return compra

    def cancelar_compra(self, compra_id: int, motivo: str, usuario_id: int | None = None) -> Compra:
        compra = self._obter(compra_id)
        if compra.status == "CANCELADA":
            raise ValueError("Compra ja cancelada.")
        validar_obrigatorio(motivo, "Motivo do cancelamento")

        if compra.status == "RECEBIDA":
            # Devolve a mercadoria: falha com "Estoque insuficiente" se parte ja foi vendida.
            for item in compra.itens:
                self.estoque_service.movimentar(
                    produto_id=item.produto_id,
                    tipo="SAIDA",
                    quantidade=item.quantidade,
                    origem=f"CANCELAMENTO COMPRA:{compra.numero}",
                    usuario_id=usuario_id or compra.usuario_id,
                )
            cancelar_lancamentos_origem(self._session, "COMPRA", compra.id, usuario_id)
        compra.status = "CANCELADA"
        compra.motivo_cancelamento = motivo.strip()
        return compra

    # -- internos ---------------------------------------------------------------------------
    def _obter(self, compra_id: int) -> Compra:
        compra = self.compra_repository.buscar_por_id(int(compra_id))
        if compra is None:
            raise ValueError("Compra nao encontrada.")
        return compra

    def _obter_editavel(self, compra_id: int) -> Compra:
        compra = self._obter(compra_id)
        if compra.status != "ABERTA":
            raise ValueError(f"Compra {compra.status.lower()} nao permite alterar itens.")
        return compra

    def _obter_item(self, item_id: int) -> ItemCompra:
        item = self.item_repository.buscar_por_id(int(item_id))
        if item is None:
            raise ValueError("Item nao encontrado.")
        return item
