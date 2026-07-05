from app.repositories.usuario_repository import UsuarioRepository
from app.utils.security import verificar_senha


class AuthService:
    def __init__(self, usuario_repository: UsuarioRepository) -> None:
        self.usuario_repository = usuario_repository

    def autenticar(self, login: str, senha: str):
        usuario = self.usuario_repository.buscar_por_login(login.strip())
        if usuario is None or not usuario.ativo:
            return None
        if not verificar_senha(senha, usuario.senha_hash):
            return None
        return usuario
