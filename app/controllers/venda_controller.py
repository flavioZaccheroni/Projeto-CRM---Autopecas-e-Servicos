from app.database.database import SessionLocal
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.venda_repository import (
    FinanceiroLancamentoRepository,
    ItemVendaRepository,
    VendaRepository,
)
from app.services.estoque_service import EstoqueService
from app.services.venda_service import VendaService


class VendaController:
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    def criar_venda(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            dados = dict(dados)
            dados["usuario_id"] = usuario_id
            venda = _service(session).criar_venda(dados)
            session.commit()
            return venda

    def adicionar_item(self, dados: dict):
        with SessionLocal() as session:
            item = _service(session).adicionar_item(
                venda_id=int(dados["venda_id"]),
                produto_id=int(dados["produto_id"]),
                quantidade=dados["quantidade"],
                valor_unitario=dados["valor_unitario"],
            )
            session.commit()
            return item

    def finalizar_venda(self, venda_id: int, usuario_id: int | None = None, data_vencimento=None):
        with SessionLocal() as session:
            venda = _service(session).finalizar_venda(venda_id, usuario_id, data_vencimento)
            session.commit()
            return venda


def _service(session) -> VendaService:
    estoque_service = EstoqueService(
        EstoqueRepository(session),
        MovimentacaoEstoqueRepository(session),
    )
    return VendaService(
        VendaRepository(session),
        ItemVendaRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    )
