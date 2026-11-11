from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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

    def listar(self) -> list[Usuario]:
        return list(self.session.scalars(select(Usuario).options(selectinload(Usuario.perfil)).order_by(Usuario.nome)))

    def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        return self.session.get(Usuario, int(usuario_id))

    def contar_admins_ativos(self, perfil_admin_id: int) -> int:
        return len(
            list(self.session.scalars(select(Usuario).where(Usuario.perfil_id == perfil_admin_id, Usuario.ativo.is_(True))))
        )

    def buscar_por_email(self, email: str) -> Usuario | None:
        return self.session.scalar(select(Usuario).where(Usuario.email == email))

    def salvar(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.flush()
        return usuario
