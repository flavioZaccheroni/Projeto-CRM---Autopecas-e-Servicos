from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class ItemOS(Base):
    __tablename__ = "itens_os"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produtos.id"))
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    ordem_servico = relationship("OrdemServico", back_populates="itens")
    produto = relationship("Produto")
