from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.perfil import Perfil


class PerfilRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar_por_nome(self, nome: str) -> Perfil | None:
        return self.session.scalar(select(Perfil).where(Perfil.nome == nome))

    def salvar(self, perfil: Perfil) -> Perfil:
        self.session.add(perfil)
        self.session.flush()
        return perfil
