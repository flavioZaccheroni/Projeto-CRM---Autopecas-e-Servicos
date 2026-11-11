from app.controllers._base import auditar, usuario_atual
from app.database.database import SessionLocal
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.services.estoque_service import EstoqueService
from app.utils.sessao import requer_permissao


def _service(session) -> EstoqueService:
    return EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))


class EstoqueController:
    @requer_permissao("estoque", "ver")
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    @requer_permissao("estoque", "ver")
    def listar_movimentacoes(self):
        with SessionLocal() as session:
            return _service(session).listar_movimentacoes()

    @requer_permissao("estoque", "criar")
    def movimentar(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            movimento = _service(session).movimentar(
                produto_id=int(dados["produto_id"]),
                tipo=dados["tipo"],
                quantidade=dados["quantidade"],
                origem=dados.get("origem") or "MANUAL",
                usuario_id=usuario_atual(usuario_id),
                localizacao=dados.get("localizacao"),
            )
            auditar(session, "estoque", movimento.tipo, f"produto={movimento.produto_id} qtd={movimento.quantidade}", movimento.id)
            session.commit()
            return movimento
