from app.database.database import SessionLocal, create_database
from app.models.perfil import Perfil
from app.repositories.perfil_repository import PerfilRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.usuario_service import UsuarioService


def initialize_database() -> None:
    create_database()
    with SessionLocal() as session:
        perfil_repository = PerfilRepository(session)
        usuario_repository = UsuarioRepository(session)

        admin_perfil = perfil_repository.buscar_por_nome("Administrador")
        if admin_perfil is None:
            admin_perfil = Perfil(
                nome="Administrador",
                descricao="Perfil com acesso administrativo inicial",
                ativo=True,
            )
            perfil_repository.salvar(admin_perfil)

        usuario_service = UsuarioService(usuario_repository)
        if usuario_repository.buscar_por_login("admin") is None:
            usuario_service.criar_usuario(
                nome="Administrador",
                email="admin@local.test",
                login="admin",
                senha="admin123",
                perfil_id=admin_perfil.id,
            )
        session.commit()
