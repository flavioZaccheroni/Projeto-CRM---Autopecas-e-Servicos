from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session


ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def listar(self) -> list[ModelT]:
        return list(self.session.scalars(select(self.model).order_by(self.model.id)))

    def buscar_por_id(self, item_id: int) -> ModelT | None:
        return self.session.get(self.model, item_id)

    def salvar(self, item: ModelT) -> ModelT:
        self.session.add(item)
        self.session.flush()
        return item

    def excluir(self, item: ModelT) -> None:
        self.session.delete(item)
        self.session.flush()
