from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.utils.datas import agora


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    data_venda: Mapped[datetime] = mapped_column(DateTime, default=agora, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ORCAMENTO", nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    desconto: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    acrescimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    forma_pagamento: Mapped[str | None] = mapped_column(String(30))
    parcelas: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(255))

    cliente = relationship("Cliente")
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
    usuario = relationship("Usuario")
