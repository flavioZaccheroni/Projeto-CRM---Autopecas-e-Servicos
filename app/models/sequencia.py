from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Sequencia(Base):
    """Contador por tipo de documento (VENDA, OS, COMPRA) para numeracao automatica."""

    __tablename__ = "sequencias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    ultimo_numero: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
