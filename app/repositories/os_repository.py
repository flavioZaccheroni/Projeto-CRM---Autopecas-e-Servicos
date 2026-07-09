from sqlalchemy.orm import Session

from app.models.item_os import ItemOS
from app.models.ordem_servico import OrdemServico
from app.repositories.base_repository import BaseRepository


class OrdemServicoRepository(BaseRepository[OrdemServico]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, OrdemServico)


class ItemOSRepository(BaseRepository[ItemOS]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ItemOS)
