from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Permissao(Base):
    __tablename__ = "permissoes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfis.id"), nullable=False)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False)
    pode_ver: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pode_criar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pode_editar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pode_excluir: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    perfil = relationship("Perfil", back_populates="permissoes")
