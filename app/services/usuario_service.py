from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.utils.security import gerar_hash_senha
from app.utils.validators import validar_email, validar_obrigatorio


class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository) -> None:
        self.usuario_repository = usuario_repository

    def criar_usuario(
        self,
        nome: str,
        email: str,
        login: str,
        senha: str,
        perfil_id: int,
    ) -> Usuario:
        validar_obrigatorio(nome, "Nome")
        validar_obrigatorio(email, "E-mail")
        validar_obrigatorio(login, "Login")
        validar_obrigatorio(senha, "Senha")
        validar_email(email)

        if self.usuario_repository.buscar_por_login(login):
            raise ValueError("Login ja cadastrado.")
        if self.usuario_repository.buscar_por_email(email):
            raise ValueError("E-mail ja cadastrado.")

        usuario = Usuario(
            nome=nome.strip(),
            email=email.strip().lower(),
            login=login.strip(),
            senha_hash=gerar_hash_senha(senha),
            perfil_id=perfil_id,
            ativo=True,
        )
        return self.usuario_repository.salvar(usuario)
