from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    data_abertura: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ABERTA", nullable=False)
    defeito_relatado: Mapped[str | None] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))

    cliente = relationship("Cliente")
    veiculo = relationship("Veiculo")
    itens = relationship("ItemOS", back_populates="ordem_servico", cascade="all, delete-orphan")
    usuario = relationship("Usuario")
