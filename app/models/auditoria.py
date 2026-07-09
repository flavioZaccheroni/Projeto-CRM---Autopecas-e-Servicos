from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    entidade: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_id: Mapped[int | None] = mapped_column(Integer)
    acao: Mapped[str] = mapped_column(String(80), nullable=False)
    detalhes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario")
