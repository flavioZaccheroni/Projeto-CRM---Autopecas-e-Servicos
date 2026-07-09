from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria
from app.models.configuracao import Configuracao
from app.repositories.base_repository import BaseRepository


class AuditoriaRepository(BaseRepository[Auditoria]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Auditoria)


class ConfiguracaoRepository(BaseRepository[Configuracao]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Configuracao)

    def buscar_por_chave(self, chave: str) -> Configuracao | None:
        return self.session.scalar(select(Configuracao).where(Configuracao.chave == chave))
