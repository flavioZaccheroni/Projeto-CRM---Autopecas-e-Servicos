from app.database.database import SessionLocal
from app.repositories.compra_repository import CompraRepository, ItemCompraRepository
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.services.compra_service import CompraService
from app.services.estoque_service import EstoqueService


class CompraController:
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    def criar_compra(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            dados = dict(dados)
            dados["usuario_id"] = usuario_id
            compra = _service(session).criar_compra(dados)
            session.commit()
            return compra

    def adicionar_item(self, dados: dict):
        with SessionLocal() as session:
            item = _service(session).adicionar_item(
                compra_id=int(dados["compra_id"]),
                produto_id=int(dados["produto_id"]),
                quantidade=dados["quantidade"],
                valor_unitario=dados["valor_unitario"],
            )
            session.commit()
            return item

    def receber_compra(self, compra_id: int, usuario_id: int | None = None):
        with SessionLocal() as session:
            compra = _service(session).receber_compra(compra_id, usuario_id)
            session.commit()
            return compra


def _service(session) -> CompraService:
    estoque_service = EstoqueService(
        EstoqueRepository(session),
        MovimentacaoEstoqueRepository(session),
    )
    return CompraService(CompraRepository(session), ItemCompraRepository(session), estoque_service)
