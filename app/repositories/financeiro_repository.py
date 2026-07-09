from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.repositories.base_repository import BaseRepository


class FinanceiroRepository(BaseRepository[FinanceiroLancamento]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, FinanceiroLancamento)

    def listar_por_status(self, status: str) -> list[FinanceiroLancamento]:
        return list(
            self.session.scalars(
                select(FinanceiroLancamento)
                .where(FinanceiroLancamento.status == status)
                .order_by(FinanceiroLancamento.data_vencimento)
            )
        )


class CaixaMovimentacaoRepository(BaseRepository[CaixaMovimentacao]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CaixaMovimentacao)
