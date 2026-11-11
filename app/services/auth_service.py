from datetime import timedelta

from app.repositories.usuario_repository import UsuarioRepository
from app.utils.datas import agora
from app.utils.security import verificar_senha

MAX_TENTATIVAS = 5
MINUTOS_BLOQUEIO = 5


class AuthService:
    def __init__(self, usuario_repository: UsuarioRepository) -> None:
        self.usuario_repository = usuario_repository

    def autenticar(self, login: str, senha: str):
        """Retorna o usuario autenticado ou None.

        Levanta ValueError quando a conta esta temporariamente bloqueada por tentativas
        erradas. O chamador deve fazer commit mesmo em caso de falha, para persistir o
        contador de tentativas.
        """
        usuario = self.usuario_repository.buscar_por_login((login or "").strip())
        if usuario is None or not usuario.ativo:
            return None

        agora_utc = agora()
        if usuario.bloqueado_ate and usuario.bloqueado_ate > agora_utc:
            minutos = int((usuario.bloqueado_ate - agora_utc).total_seconds() // 60) + 1
            raise ValueError(f"Conta bloqueada por tentativas invalidas. Tente novamente em {minutos} minuto(s).")

        if not verificar_senha(senha or "", usuario.senha_hash):
            usuario.tentativas_falhas = (usuario.tentativas_falhas or 0) + 1
            if usuario.tentativas_falhas >= MAX_TENTATIVAS:
                usuario.bloqueado_ate = agora_utc + timedelta(minutes=MINUTOS_BLOQUEIO)
                usuario.tentativas_falhas = 0
            self.usuario_repository.salvar(usuario)
            return None

        usuario.tentativas_falhas = 0
        usuario.bloqueado_ate = None
        self.usuario_repository.salvar(usuario)
        return usuario
