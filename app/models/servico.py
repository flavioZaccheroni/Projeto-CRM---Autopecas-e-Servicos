from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Servico(Base):
    """Catalogo de servicos (mao de obra): preco padrao e tempo estimado, usados ao montar a OS."""

    __tablename__ = "servicos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    preco_padrao: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    tempo_estimado_min: Mapped[int | None] = mapped_column(Integer)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __str__(self) -> str:
        return self.nome
