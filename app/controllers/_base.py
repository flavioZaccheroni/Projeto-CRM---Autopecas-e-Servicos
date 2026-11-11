"""Utilitarios compartilhados pelos controllers: auditoria de escrita."""

from app.repositories.seguranca_repository import AuditoriaRepository
from app.services.seguranca_service import AuditoriaService
from app.utils.sessao import Sessao


def auditar(session, entidade: str, acao: str, detalhes: str | None = None, entidade_id: int | None = None) -> None:
    """Registra uma acao de escrita na auditoria, atribuida ao usuario logado."""
    AuditoriaService(AuditoriaRepository(session)).registrar(
        entidade=entidade,
        acao=acao,
        detalhes=detalhes,
        usuario_id=Sessao.usuario_id,
        entidade_id=entidade_id,
    )


def usuario_atual(usuario_id: int | None = None) -> int | None:
    """Usuario responsavel: o logado na sessao, ou o informado quando nao ha sessao."""
    return Sessao.usuario_id if Sessao.usuario_id is not None else usuario_id
