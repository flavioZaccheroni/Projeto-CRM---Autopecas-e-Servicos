from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    data_venda: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ORCAMENTO", nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    cliente = relationship("Cliente")
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
    usuario = relationship("Usuario")
