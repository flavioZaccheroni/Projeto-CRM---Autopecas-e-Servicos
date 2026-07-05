from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class FinanceiroLancamento(Base):
    __tablename__ = "financeiro_lancamentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    origem: Mapped[str] = mapped_column(String(80), nullable=False)
    origem_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    fornecedor_id: Mapped[int | None] = mapped_column(ForeignKey("fornecedores.id"))
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="ABERTO", nullable=False)

    cliente = relationship("Cliente")
    fornecedor = relationship("Fornecedor")
