from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base
from app.utils.datas import agora


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    login: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfis.id"), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora, nullable=False)
    precisa_trocar_senha: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tentativas_falhas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime)

    perfil = relationship("Perfil", back_populates="usuarios")
