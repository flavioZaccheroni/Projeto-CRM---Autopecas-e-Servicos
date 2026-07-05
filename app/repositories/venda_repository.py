from sqlalchemy.orm import Session

from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.item_venda import ItemVenda
from app.models.venda import Venda
from app.repositories.base_repository import BaseRepository


class VendaRepository(BaseRepository[Venda]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Venda)


class ItemVendaRepository(BaseRepository[ItemVenda]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ItemVenda)


class FinanceiroLancamentoRepository(BaseRepository[FinanceiroLancamento]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, FinanceiroLancamento)
