from app.database.database import SessionLocal
from app.services.dashboard_service import DashboardService
from app.utils.sessao import Sessao


class DashboardController:
    def resumo(self) -> dict:
        """Indicadores liberados para o perfil: secoes sem permissao 'ver' vem como None."""
        Sessao.exigir_autenticado()
        with SessionLocal() as session:
            servico = DashboardService(session)
            return {
                "vendas": servico.vendas() if Sessao.pode("vendas", "ver") else None,
                "financeiro": servico.financeiro() if Sessao.pode("financeiro", "ver") else None,
                "estoque_baixo": servico.estoque_baixo() if Sessao.pode("estoque", "ver") else None,
            }
