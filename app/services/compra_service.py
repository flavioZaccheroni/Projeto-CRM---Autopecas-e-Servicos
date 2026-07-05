from datetime import date
from decimal import Decimal

from app.models.compra import Compra
from app.models.item_compra import ItemCompra
from app.repositories.compra_repository import CompraRepository, ItemCompraRepository
from app.services.estoque_service import EstoqueService
from app.utils.validators import validar_obrigatorio


class CompraService:
    def __init__(
        self,
        compra_repository: CompraRepository,
        item_repository: ItemCompraRepository,
        estoque_service: EstoqueService,
    ) -> None:
        self.compra_repository = compra_repository
        self.item_repository = item_repository
        self.estoque_service = estoque_service

    def listar(self) -> list[Compra]:
        return self.compra_repository.listar()

    def criar_compra(self, dados: dict) -> Compra:
        validar_obrigatorio(dados.get("fornecedor_id"), "Fornecedor")
        validar_obrigatorio(dados.get("numero"), "Numero")
        compra = Compra(
            fornecedor_id=int(dados["fornecedor_id"]),
            numero=str(dados["numero"]).strip(),
            data_compra=_parse_data(dados.get("data_compra")),
            status=dados.get("status") or "ABERTA",
            valor_total=Decimal("0"),
            usuario_id=dados.get("usuario_id"),
        )
        return self.compra_repository.salvar(compra)

    def adicionar_item(self, compra_id: int, produto_id: int, quantidade, valor_unitario) -> ItemCompra:
        compra = self.compra_repository.buscar_por_id(int(compra_id))
        if compra is None:
            raise ValueError("Compra nao encontrada.")
        if compra.status == "RECEBIDA":
            raise ValueError("Compra recebida nao permite novos itens.")

        quantidade_decimal = Decimal(str(quantidade).replace(",", "."))
        valor_unitario_decimal = Decimal(str(valor_unitario).replace(",", "."))
        if quantidade_decimal <= 0 or valor_unitario_decimal < 0:
            raise ValueError("Quantidade e valor unitario invalidos.")

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

    def receber_compra(self, compra_id: int, usuario_id: int | None = None) -> Compra:
        compra = self.compra_repository.buscar_por_id(int(compra_id))
        if compra is None:
            raise ValueError("Compra nao encontrada.")
        if not compra.itens:
            raise ValueError("Compra precisa ter pelo menos um item para recebimento.")
        if compra.status == "RECEBIDA":
            raise ValueError("Compra ja recebida.")

        for item in compra.itens:
            self.estoque_service.movimentar(
                produto_id=item.produto_id,
                tipo="ENTRADA",
                quantidade=item.quantidade,
                origem=f"COMPRA:{compra.numero}",
                usuario_id=usuario_id or compra.usuario_id,
            )
        compra.status = "RECEBIDA"
        return compra


def _parse_data(valor) -> date:
    if isinstance(valor, date):
        return valor
    if not valor:
        return date.today()
    return date.fromisoformat(str(valor))
