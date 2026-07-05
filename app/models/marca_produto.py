from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class MarcaProduto(Base):
    __tablename__ = "marcas_produto"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    produtos = relationship("Produto", back_populates="marca")

    def __str__(self) -> str:
        return self.nome
