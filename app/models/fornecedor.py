from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    razao_social: Mapped[str] = mapped_column(String(160), nullable=False)
    nome_fantasia: Mapped[str | None] = mapped_column(String(160))
    cnpj: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(150))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    compras = relationship("Compra", back_populates="fornecedor")

    def __str__(self) -> str:
        return self.nome_fantasia or self.razao_social
