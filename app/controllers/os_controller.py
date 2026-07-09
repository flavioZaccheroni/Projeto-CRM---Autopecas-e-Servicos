from app.database.database import SessionLocal
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.os_repository import ItemOSRepository, OrdemServicoRepository
from app.repositories.venda_repository import FinanceiroLancamentoRepository
from app.services.estoque_service import EstoqueService
from app.services.os_service import OrdemServicoService


class OrdemServicoController:
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    def abrir_os(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            dados = dict(dados)
            dados["usuario_id"] = usuario_id
            ordem = _service(session).abrir_os(dados)
            session.commit()
            return ordem

    def adicionar_item(self, dados: dict):
        with SessionLocal() as session:
            item = _service(session).adicionar_item(
                os_id=int(dados["os_id"]),
                tipo=dados["tipo"],
                produto_id=dados.get("produto_id"),
                descricao=dados["descricao"],
                quantidade=dados["quantidade"],
                valor_unitario=dados["valor_unitario"],
            )
            session.commit()
            return item

    def finalizar_os(self, os_id: int, usuario_id: int | None = None, data_vencimento=None):
        with SessionLocal() as session:
            ordem = _service(session).finalizar_os(os_id, usuario_id, data_vencimento)
            session.commit()
            return ordem


def _service(session) -> OrdemServicoService:
    estoque_service = EstoqueService(
        EstoqueRepository(session),
        MovimentacaoEstoqueRepository(session),
    )
    return OrdemServicoService(
        OrdemServicoRepository(session),
        ItemOSRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    )
