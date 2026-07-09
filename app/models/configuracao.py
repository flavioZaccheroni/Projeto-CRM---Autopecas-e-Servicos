from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    valor: Mapped[str | None] = mapped_column(Text)
