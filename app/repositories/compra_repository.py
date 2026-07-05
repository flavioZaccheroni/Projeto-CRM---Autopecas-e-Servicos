from sqlalchemy.orm import Session

from app.models.compra import Compra
from app.models.item_compra import ItemCompra
from app.repositories.base_repository import BaseRepository


class CompraRepository(BaseRepository[Compra]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Compra)


class ItemCompraRepository(BaseRepository[ItemCompra]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ItemCompra)
