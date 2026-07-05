from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Compra(Base):
    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    data_compra: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ABERTA", nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    fornecedor = relationship("Fornecedor", back_populates="compras")
    itens = relationship("ItemCompra", back_populates="compra", cascade="all, delete-orphan")
    usuario = relationship("Usuario")
