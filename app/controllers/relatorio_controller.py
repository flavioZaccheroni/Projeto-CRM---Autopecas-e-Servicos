from app.database.database import SessionLocal
from app.models.caixa_movimentacao import CaixaMovimentacao
from app.models.estoque import Estoque
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.ordem_servico import OrdemServico
from app.models.venda import Venda
from app.repositories.base_repository import BaseRepository
from app.services.relatorio_service import RelatorioService


class RelatorioController:
    def gerar(self, tipo: str, formato: str):
        with SessionLocal() as session:
            service = RelatorioService(
                BaseRepository(session, Venda),
                BaseRepository(session, Estoque),
                BaseRepository(session, OrdemServico),
                BaseRepository(session, FinanceiroLancamento),
                BaseRepository(session, CaixaMovimentacao),
            )
            return service.gerar(tipo, formato)
