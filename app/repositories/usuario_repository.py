from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar_por_login(self, login: str) -> Usuario | None:
        return self.session.scalar(
            select(Usuario)
            .options(selectinload(Usuario.perfil))
            .where(Usuario.login == login)
        )

    def buscar_por_email(self, email: str) -> Usuario | None:
        return self.session.scalar(select(Usuario).where(Usuario.email == email))

    def salvar(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.flush()
        return usuario
