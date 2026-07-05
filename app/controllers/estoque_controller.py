from app.database.database import SessionLocal
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.services.estoque_service import EstoqueService


class EstoqueController:
    def listar(self):
        with SessionLocal() as session:
            return EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session)).listar()

    def listar_movimentacoes(self):
        with SessionLocal() as session:
            return EstoqueService(
                EstoqueRepository(session),
                MovimentacaoEstoqueRepository(session),
            ).listar_movimentacoes()

    def movimentar(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            movimento = EstoqueService(
                EstoqueRepository(session),
                MovimentacaoEstoqueRepository(session),
            ).movimentar(
                produto_id=int(dados["produto_id"]),
                tipo=dados["tipo"],
                quantidade=dados["quantidade"],
                origem=dados.get("origem") or "MANUAL",
                usuario_id=usuario_id,
                localizacao=dados.get("localizacao"),
            )
            session.commit()
            return movimento
