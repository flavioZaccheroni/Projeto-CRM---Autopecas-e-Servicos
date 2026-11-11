from app.controllers._base import auditar
from app.database.database import SessionLocal
from app.repositories.usuario_repository import UsuarioRepository
from app.services.permissao_service import PermissaoService
from app.services.usuario_service import UsuarioService
from app.utils.sessao import requer_permissao


class UsuarioController:
    @requer_permissao("usuarios", "ver")
    def listar(self):
        with SessionLocal() as session:
            return UsuarioService(UsuarioRepository(session)).listar()

    @requer_permissao("usuarios", "ver")
    def listar_perfis(self):
        with SessionLocal() as session:
            return PermissaoService(session).listar_perfis()

    @requer_permissao("usuarios", "criar")
    def criar(self, nome: str, email: str, login: str, senha: str, perfil_id: int):
        with SessionLocal() as session:
            usuario = UsuarioService(UsuarioRepository(session)).criar_usuario(
                nome, email, login, senha, int(perfil_id), precisa_trocar_senha=True
            )
            auditar(session, "usuario", "CRIAR", login, usuario.id)
            session.commit()
            return usuario

    @requer_permissao("usuarios", "editar")
    def atualizar(self, usuario_id: int, nome: str, email: str, perfil_id: int, ativo: bool):
        with SessionLocal() as session:
            usuario = UsuarioService(UsuarioRepository(session)).atualizar_usuario(
                usuario_id, nome, email, perfil_id, ativo
            )
            auditar(session, "usuario", "EDITAR", usuario.login, usuario.id)
            session.commit()
            return usuario

    @requer_permissao("usuarios", "editar")
    def redefinir_senha(self, usuario_id: int, nova_senha: str):
        with SessionLocal() as session:
            usuario = UsuarioService(UsuarioRepository(session)).redefinir_senha(usuario_id, nova_senha)
            auditar(session, "usuario", "REDEFINIR_SENHA", usuario.login, usuario.id)
            session.commit()
            return usuario

    @requer_permissao("usuarios", "editar")
    def desbloquear(self, usuario_id: int):
        with SessionLocal() as session:
            usuario = UsuarioService(UsuarioRepository(session)).desbloquear(usuario_id)
            auditar(session, "usuario", "DESBLOQUEAR", usuario.login, usuario.id)
            session.commit()
            return usuario


class PermissaoController:
    @requer_permissao("permissoes", "ver")
    def listar_perfis(self):
        with SessionLocal() as session:
            return PermissaoService(session).listar_perfis()

    @requer_permissao("permissoes", "ver")
    def carregar(self, perfil_id: int):
        with SessionLocal() as session:
            return PermissaoService(session).carregar(perfil_id)

    @requer_permissao("permissoes", "criar")
    def criar_perfil(self, nome: str, descricao: str | None = None):
        with SessionLocal() as session:
            perfil = PermissaoService(session).criar_perfil(nome, descricao)
            auditar(session, "perfil", "CRIAR", nome, perfil.id)
            session.commit()
            return perfil

    @requer_permissao("permissoes", "editar")
    def salvar_matriz(self, perfil_id: int, matriz: dict[str, set[str]]):
        with SessionLocal() as session:
            PermissaoService(session).salvar_matriz(perfil_id, matriz)
            auditar(session, "perfil", "PERMISSOES", entidade_id=perfil_id)
            session.commit()
