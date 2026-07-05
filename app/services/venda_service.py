from datetime import date, datetime
from decimal import Decimal

from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.item_venda import ItemVenda
from app.models.venda import Venda
from app.repositories.venda_repository import (
    FinanceiroLancamentoRepository,
    ItemVendaRepository,
    VendaRepository,
)
from app.services.estoque_service import EstoqueService
from app.utils.validators import validar_obrigatorio


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

    def listar(self) -> list[Venda]:
        return self.venda_repository.listar()

    def criar_venda(self, dados: dict) -> Venda:
        validar_obrigatorio(dados.get("cliente_id"), "Cliente")
        validar_obrigatorio(dados.get("numero"), "Numero")
        venda = Venda(
            cliente_id=int(dados["cliente_id"]),
            numero=str(dados["numero"]).strip(),
            data_venda=_parse_data_hora(dados.get("data_venda")),
            status=dados.get("status") or "ORCAMENTO",
            valor_total=Decimal("0"),
            usuario_id=dados.get("usuario_id"),
        )
        return self.venda_repository.salvar(venda)

    def adicionar_item(self, venda_id: int, produto_id: int, quantidade, valor_unitario) -> ItemVenda:
        venda = self.venda_repository.buscar_por_id(int(venda_id))
        if venda is None:
            raise ValueError("Venda nao encontrada.")
        if venda.status == "FINALIZADA":
            raise ValueError("Venda finalizada nao permite novos itens.")

        quantidade_decimal = Decimal(str(quantidade).replace(",", "."))
        valor_unitario_decimal = Decimal(str(valor_unitario).replace(",", "."))
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

    def finalizar_venda(self, venda_id: int, usuario_id: int | None = None, data_vencimento=None) -> Venda:
        venda = self.venda_repository.buscar_por_id(int(venda_id))
        if venda is None:
            raise ValueError("Venda nao encontrada.")
        if not venda.itens:
            raise ValueError("Venda precisa ter pelo menos um item para finalizacao.")
        if venda.status == "FINALIZADA":
            raise ValueError("Venda ja finalizada.")

        for item in venda.itens:
            self.estoque_service.movimentar(
                produto_id=item.produto_id,
                tipo="SAIDA",
                quantidade=item.quantidade,
                origem=f"VENDA:{venda.numero}",
                usuario_id=usuario_id or venda.usuario_id,
            )

        venda.status = "FINALIZADA"
        lancamento = FinanceiroLancamento(
            tipo="RECEBER",
            origem="VENDA",
            origem_id=venda.id,
            cliente_id=venda.cliente_id,
            fornecedor_id=None,
            descricao=f"Venda {venda.numero}",
            valor=venda.valor_total,
            data_vencimento=_parse_data(data_vencimento),
            status="ABERTO",
        )
        self.financeiro_repository.salvar(lancamento)
        return venda


def _parse_data_hora(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if not valor:
        return datetime.utcnow()
    return datetime.fromisoformat(str(valor))


def _parse_data(valor) -> date:
    if isinstance(valor, date):
        return valor
    if not valor:
        return date.today()
    return date.fromisoformat(str(valor))
