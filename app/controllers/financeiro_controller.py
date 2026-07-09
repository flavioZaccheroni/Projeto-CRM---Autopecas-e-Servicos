from app.database.database import SessionLocal
from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository
from app.services.financeiro_service import FinanceiroService


class FinanceiroController:
    def listar_lancamentos(self):
        with SessionLocal() as session:
            return _service(session).listar_lancamentos()

    def listar_caixa(self):
        with SessionLocal() as session:
            return _service(session).listar_caixa()

    def criar_lancamento(self, dados: dict):
        with SessionLocal() as session:
            lancamento = _service(session).criar_lancamento(dados)
            session.commit()
            return lancamento

    def baixar_lancamento(self, lancamento_id: int, forma_pagamento: str, usuario_id: int | None = None, data_pagamento=None):
        with SessionLocal() as session:
            lancamento = _service(session).baixar_lancamento(lancamento_id, forma_pagamento, usuario_id, data_pagamento)
            session.commit()
            return lancamento

    def estornar_lancamento(self, lancamento_id: int, usuario_id: int | None = None):
        with SessionLocal() as session:
            lancamento = _service(session).estornar_lancamento(lancamento_id, usuario_id)
            session.commit()
            return lancamento

    def resumo_fluxo(self):
        with SessionLocal() as session:
            return _service(session).resumo_fluxo()


def _service(session) -> FinanceiroService:
    return FinanceiroService(
        FinanceiroRepository(session),
        CaixaMovimentacaoRepository(session),
    )
