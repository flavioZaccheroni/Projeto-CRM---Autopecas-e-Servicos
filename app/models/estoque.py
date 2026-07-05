from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Estoque(Base):
    __tablename__ = "estoque"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), unique=True, nullable=False)
    quantidade_atual: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0, nullable=False)
    localizacao: Mapped[str | None] = mapped_column(String(80))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    produto = relationship("Produto", back_populates="estoque")
