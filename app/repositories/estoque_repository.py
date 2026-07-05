from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.estoque import Estoque
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.repositories.base_repository import BaseRepository


class EstoqueRepository(BaseRepository[Estoque]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Estoque)

    def buscar_por_produto(self, produto_id: int) -> Estoque | None:
        return self.session.scalar(select(Estoque).where(Estoque.produto_id == produto_id))


class MovimentacaoEstoqueRepository(BaseRepository[MovimentacaoEstoque]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MovimentacaoEstoque)

    def listar_por_produto(self, produto_id: int) -> list[MovimentacaoEstoque]:
        return list(
            self.session.scalars(
                select(MovimentacaoEstoque)
                .where(MovimentacaoEstoque.produto_id == produto_id)
                .order_by(MovimentacaoEstoque.criado_em.desc())
            )
        )
