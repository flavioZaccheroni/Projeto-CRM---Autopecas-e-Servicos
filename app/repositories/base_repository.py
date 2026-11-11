from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    # Relacionamentos carregados junto com a listagem (as telas exibem nomes, nao so IDs).
    eager_load: tuple[str, ...] = ()

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def listar(self) -> list[ModelT]:
        consulta = select(self.model).order_by(self.model.id)
        for nome in self.eager_load:
            consulta = consulta.options(selectinload(getattr(self.model, nome)))
        return list(self.session.scalars(consulta))

    def buscar_por_id(self, item_id: int) -> ModelT | None:
        return self.session.get(self.model, item_id)

    def salvar(self, item: ModelT) -> ModelT:
        self.session.add(item)
        self.session.flush()
        return item

    def excluir(self, item: ModelT) -> None:
        self.session.delete(item)
        self.session.flush()
