from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.utils.security import gerar_hash_senha, verificar_senha
from app.utils.validators import validar_email, validar_obrigatorio, validar_senha_forte


class UsuarioService:
    def __init__(self, usuario_repository: UsuarioRepository) -> None:
        self.usuario_repository = usuario_repository

    def listar(self) -> list[Usuario]:
        return self.usuario_repository.listar()

    def criar_usuario(
        self,
        nome: str,
        email: str,
        login: str,
        senha: str,
        perfil_id: int,
        precisa_trocar_senha: bool = False,
    ) -> Usuario:
        validar_obrigatorio(nome, "Nome")
        validar_obrigatorio(email, "E-mail")
        validar_obrigatorio(login, "Login")
        validar_obrigatorio(senha, "Senha")
        validar_obrigatorio(perfil_id, "Perfil")
        validar_email(email)
        validar_senha_forte(senha)

        if self.usuario_repository.buscar_por_login(login.strip()):
            raise ValueError("Login ja cadastrado.")
        if self.usuario_repository.buscar_por_email(email.strip().lower()):
            raise ValueError("E-mail ja cadastrado.")

        usuario = Usuario(
            nome=nome.strip(),
            email=email.strip().lower(),
            login=login.strip(),
            senha_hash=gerar_hash_senha(senha),
            perfil_id=int(perfil_id),
            ativo=True,
            precisa_trocar_senha=precisa_trocar_senha,
        )
        return self.usuario_repository.salvar(usuario)

    def atualizar_usuario(self, usuario_id: int, nome: str, email: str, perfil_id: int, ativo: bool) -> Usuario:
        usuario = self._obter(usuario_id)
        validar_obrigatorio(nome, "Nome")
        validar_obrigatorio(email, "E-mail")
        validar_email(email)
        email = email.strip().lower()
        existente = self.usuario_repository.buscar_por_email(email)
        if existente and existente.id != usuario.id:
            raise ValueError("E-mail ja cadastrado.")
        if not ativo or int(perfil_id) != usuario.perfil_id:
            self._garantir_admin_restante(usuario, novo_ativo=ativo, novo_perfil_id=int(perfil_id))
        usuario.nome = nome.strip()
        usuario.email = email
        usuario.perfil_id = int(perfil_id)
        usuario.ativo = bool(ativo)
        return self.usuario_repository.salvar(usuario)

    def redefinir_senha(self, usuario_id: int, nova_senha: str) -> Usuario:
        """Redefinicao feita por um administrador: o usuario precisara trocar a senha no proximo login."""
        usuario = self._obter(usuario_id)
        validar_senha_forte(nova_senha)
        usuario.senha_hash = gerar_hash_senha(nova_senha)
        usuario.precisa_trocar_senha = True
        usuario.tentativas_falhas = 0
        usuario.bloqueado_ate = None
        return self.usuario_repository.salvar(usuario)

    def alterar_senha(self, usuario_id: int, senha_atual: str, nova_senha: str) -> Usuario:
        usuario = self._obter(usuario_id)
        if not verificar_senha(senha_atual or "", usuario.senha_hash):
            raise ValueError("Senha atual incorreta.")
        validar_senha_forte(nova_senha)
        if verificar_senha(nova_senha, usuario.senha_hash):
            raise ValueError("A nova senha deve ser diferente da atual.")
        usuario.senha_hash = gerar_hash_senha(nova_senha)
        usuario.precisa_trocar_senha = False
        return self.usuario_repository.salvar(usuario)

    def desbloquear(self, usuario_id: int) -> Usuario:
        usuario = self._obter(usuario_id)
        usuario.tentativas_falhas = 0
        usuario.bloqueado_ate = None
        return self.usuario_repository.salvar(usuario)

    # -- internos ---------------------------------------------------------------------------
    def _obter(self, usuario_id: int) -> Usuario:
        usuario = self.usuario_repository.buscar_por_id(int(usuario_id))
        if usuario is None:
            raise ValueError("Usuario nao encontrado.")
        return usuario

    def _garantir_admin_restante(self, usuario: Usuario, novo_ativo: bool, novo_perfil_id: int) -> None:
        """Impede deixar o sistema sem nenhum Administrador ativo."""
        perfil = usuario.perfil
        if perfil is None or perfil.nome != "Administrador" or not usuario.ativo:
            return
        continua_admin = novo_ativo and novo_perfil_id == usuario.perfil_id
        if not continua_admin and self.usuario_repository.contar_admins_ativos(usuario.perfil_id) <= 1:
            raise ValueError("Deve existir pelo menos um Administrador ativo.")
