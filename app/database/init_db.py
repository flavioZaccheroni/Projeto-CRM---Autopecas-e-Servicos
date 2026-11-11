from sqlalchemy import select

from app.database.database import SessionLocal, create_database
from app.models.usuario import Usuario
from app.repositories.perfil_repository import PerfilRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.permissao_service import PERFIL_ADMIN, PermissaoService
from app.services.usuario_service import UsuarioService
from app.utils.security import verificar_senha

SENHA_INICIAL = "admin123"  # temporaria: o primeiro login exige a troca


def initialize_database() -> None:
    create_database()
    with SessionLocal() as session:
        PermissaoService(session).garantir_perfis_padrao()
        admin_perfil = PerfilRepository(session).buscar_por_nome(PERFIL_ADMIN)

        usuario_repository = UsuarioRepository(session)
        if usuario_repository.buscar_por_login("admin") is None:
            UsuarioService(usuario_repository).criar_usuario(
                nome="Administrador",
                email="admin@local.test",
                login="admin",
                senha=SENHA_INICIAL,
                perfil_id=admin_perfil.id,
                precisa_trocar_senha=True,
            )

        # Bancos antigos: quem ainda usa a senha inicial passa a ser obrigado a troca-la.
        for usuario in session.scalars(select(Usuario).where(Usuario.precisa_trocar_senha.is_(False))):
            if verificar_senha(SENHA_INICIAL, usuario.senha_hash):
                usuario.precisa_trocar_senha = True
        session.commit()
