from app.controllers._base import auditar, usuario_atual
from app.database.database import SessionLocal
from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository
from app.services.financeiro_service import FinanceiroService
from app.utils.sessao import requer_permissao


def _service(session) -> FinanceiroService:
    return FinanceiroService(
        FinanceiroRepository(session),
        CaixaMovimentacaoRepository(session),
    )


class FinanceiroController:
    @requer_permissao("financeiro", "ver")
    def listar_lancamentos(self):
        with SessionLocal() as session:
            return _service(session).listar_lancamentos()

    @requer_permissao("financeiro", "ver")
    def listar_caixa(self):
        with SessionLocal() as session:
            return _service(session).listar_caixa()

    @requer_permissao("financeiro", "criar")
    def criar_lancamento(self, dados: dict):
        with SessionLocal() as session:
            lancamento = _service(session).criar_lancamento(dados)
            auditar(session, "financeiro", "CRIAR", f"{lancamento.tipo} {lancamento.valor}", lancamento.id)
            session.commit()
            return lancamento

    @requer_permissao("financeiro", "editar")
    def baixar_lancamento(self, lancamento_id: int, forma_pagamento: str, usuario_id: int | None = None, data_pagamento=None):
        with SessionLocal() as session:
            lancamento = _service(session).baixar_lancamento(
                lancamento_id, forma_pagamento, usuario_atual(usuario_id), data_pagamento
            )
            auditar(session, "financeiro", "BAIXAR", f"{lancamento.descricao} {lancamento.valor}", lancamento.id)
            session.commit()
            return lancamento

    @requer_permissao("financeiro", "excluir")
    def estornar_lancamento(self, lancamento_id: int, usuario_id: int | None = None):
        with SessionLocal() as session:
            lancamento = _service(session).estornar_lancamento(lancamento_id, usuario_atual(usuario_id))
            auditar(session, "financeiro", "ESTORNAR", f"{lancamento.descricao} {lancamento.valor}", lancamento.id)
            session.commit()
            return lancamento

    @requer_permissao("financeiro", "ver")
    def resumo_fluxo(self):
        with SessionLocal() as session:
            return _service(session).resumo_fluxo()
