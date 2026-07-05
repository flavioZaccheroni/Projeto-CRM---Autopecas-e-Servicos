from app.database.database import SessionLocal
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService


class AuthController:
    def autenticar(self, login: str, senha: str):
        with SessionLocal() as session:
            repository = UsuarioRepository(session)
            service = AuthService(repository)
            return service.autenticar(login, senha)
