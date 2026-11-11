from app.controllers._base import auditar
from app.database.database import SessionLocal
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService
from app.services.permissao_service import PERFIL_ADMIN, PermissaoService
from app.services.usuario_service import UsuarioService
from app.utils.sessao import Sessao


class AuthController:
    def autenticar(self, login: str, senha: str):
        """Autentica e inicia a sessao. Retorna o usuario ou None; ValueError se a conta estiver bloqueada."""
        with SessionLocal() as session:
            service = AuthService(UsuarioRepository(session))
            try:
                usuario = service.autenticar(login, senha)
            except ValueError:
                session.commit()
                raise
            if usuario is None:
                auditar(session, "login", "FALHA", f"login={(login or '').strip()}")
                session.commit()
                return None
            permissoes = PermissaoService(session).carregar(usuario.perfil_id)
            Sessao.iniciar(usuario, permissoes, admin=usuario.perfil.nome == PERFIL_ADMIN)
            auditar(session, "login", "ENTRAR", usuario.login, entidade_id=usuario.id)
            session.commit()
            return usuario

    def trocar_senha(self, usuario_id: int, senha_atual: str, nova_senha: str) -> None:
        with SessionLocal() as session:
            UsuarioService(UsuarioRepository(session)).alterar_senha(usuario_id, senha_atual, nova_senha)
            auditar(session, "usuario", "TROCAR_SENHA", entidade_id=usuario_id)
            session.commit()

    def encerrar_sessao(self) -> None:
        if Sessao.usuario_id is not None:
            with SessionLocal() as session:
                auditar(session, "login", "SAIR", Sessao.usuario_nome, entidade_id=Sessao.usuario_id)
                session.commit()
        Sessao.encerrar()
