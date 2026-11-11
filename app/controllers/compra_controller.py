from app.controllers._base import auditar, usuario_atual
from app.database.database import SessionLocal
from app.repositories.compra_repository import CompraRepository, ItemCompraRepository
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.venda_repository import FinanceiroLancamentoRepository
from app.services.compra_service import CompraService
from app.services.estoque_service import EstoqueService
from app.utils.sessao import requer_permissao


def _service(session) -> CompraService:
    estoque_service = EstoqueService(
        EstoqueRepository(session),
        MovimentacaoEstoqueRepository(session),
    )
    return CompraService(
        CompraRepository(session),
        ItemCompraRepository(session),
        estoque_service,
        FinanceiroLancamentoRepository(session),
    )


class CompraController:
    @requer_permissao("compras", "ver")
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    @requer_permissao("compras", "criar")
    def criar_compra(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            dados = dict(dados)
            dados["usuario_id"] = usuario_atual(usuario_id)
            compra = _service(session).criar_compra(dados)
            auditar(session, "compra", "CRIAR", compra.numero, compra.id)
            session.commit()
            return compra

    @requer_permissao("compras", "criar")
    def adicionar_item(self, dados: dict):
        with SessionLocal() as session:
            item = _service(session).adicionar_item(
                compra_id=int(dados["compra_id"]),
                produto_id=int(dados["produto_id"]),
                quantidade=dados["quantidade"],
                valor_unitario=dados["valor_unitario"],
            )
            auditar(session, "compra", "ADICIONAR_ITEM", f"produto={item.produto_id}", item.compra_id)
            session.commit()
            return item

    @requer_permissao("compras", "editar")
    def atualizar_item(self, item_id: int, quantidade, valor_unitario):
        with SessionLocal() as session:
            item = _service(session).atualizar_item(item_id, quantidade, valor_unitario)
            auditar(session, "compra", "EDITAR_ITEM", f"item={item_id}", item.compra_id)
            session.commit()
            return item

    @requer_permissao("compras", "excluir")
    def remover_item(self, item_id: int) -> None:
        with SessionLocal() as session:
            _service(session).remover_item(item_id)
            auditar(session, "compra", "REMOVER_ITEM", f"item={item_id}")
            session.commit()

    @requer_permissao("compras", "editar")
    def receber_compra(self, compra_id: int, usuario_id: int | None = None, data_vencimento=None, parcelas: int = 1):
        with SessionLocal() as session:
            compra = _service(session).receber_compra(compra_id, usuario_atual(usuario_id), data_vencimento, parcelas)
            auditar(session, "compra", "RECEBER", compra.numero, compra.id)
            session.commit()
            return compra

    @requer_permissao("compras", "excluir")
    def cancelar_compra(self, compra_id: int, motivo: str, usuario_id: int | None = None):
        with SessionLocal() as session:
            compra = _service(session).cancelar_compra(compra_id, motivo, usuario_atual(usuario_id))
            auditar(session, "compra", "CANCELAR", f"{compra.numero}: {motivo}", compra.id)
            session.commit()
            return compra
