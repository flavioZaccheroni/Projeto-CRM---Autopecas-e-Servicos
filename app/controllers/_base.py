"""Utilitarios compartilhados pelos controllers: auditoria de escrita."""

from decimal import Decimal

from app.repositories.seguranca_repository import AuditoriaRepository, ConfiguracaoRepository
from app.services._itens import CHAVE_DESCONTO_MAX, PADRAO_DESCONTO_MAX
from app.services.seguranca_service import AuditoriaService, ConfiguracaoService
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


def limite_desconto(session) -> Decimal | None:
    """Limite (%) de desconto do usuario logado: administrador sem limite; demais, parametro (padrao 10%)."""
    if Sessao.admin or Sessao.sistema:
        return None
    texto = ConfiguracaoService(ConfiguracaoRepository(session)).obter(CHAVE_DESCONTO_MAX)
    try:
        return max(Decimal("0"), Decimal(str(texto).replace(",", "."))) if texto else PADRAO_DESCONTO_MAX
    except ArithmeticError:
        return PADRAO_DESCONTO_MAX
