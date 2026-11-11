from app.controllers._base import auditar, usuario_atual
from app.database.database import SessionLocal
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.venda_repository import (
    FinanceiroLancamentoRepository,
    ItemVendaRepository,
    VendaRepository,
)
from app.services.estoque_service import EstoqueService
from app.services.venda_service import VendaService
from app.utils.sessao import requer_permissao


def _service(session) -> VendaService:
    estoque_service = EstoqueService(
        EstoqueRepository(session),
        MovimentacaoEstoqueRepository(session),
    )
    return VendaService(
        VendaRepository(session),
        ItemVendaRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    )


class VendaController:
    @requer_permissao("vendas", "ver")
    def listar(self):
        with SessionLocal() as session:
            return _service(session).listar()

    @requer_permissao("vendas", "criar")
    def criar_venda(self, dados: dict, usuario_id: int | None = None):
        with SessionLocal() as session:
            dados = dict(dados)
            dados["usuario_id"] = usuario_atual(usuario_id)
            venda = _service(session).criar_venda(dados)
            auditar(session, "venda", "CRIAR", venda.numero, venda.id)
            session.commit()
            return venda

    @requer_permissao("vendas", "criar")
    def adicionar_item(self, dados: dict):
        with SessionLocal() as session:
            item = _service(session).adicionar_item(
                venda_id=int(dados["venda_id"]),
                produto_id=int(dados["produto_id"]),
                quantidade=dados["quantidade"],
                valor_unitario=dados["valor_unitario"],
            )
            auditar(session, "venda", "ADICIONAR_ITEM", f"produto={item.produto_id}", item.venda_id)
            session.commit()
            return item

    @requer_permissao("vendas", "editar")
    def atualizar_item(self, item_id: int, quantidade, valor_unitario):
        with SessionLocal() as session:
            item = _service(session).atualizar_item(item_id, quantidade, valor_unitario)
            auditar(session, "venda", "EDITAR_ITEM", f"item={item_id}", item.venda_id)
            session.commit()
            return item

    @requer_permissao("vendas", "excluir")
    def remover_item(self, item_id: int) -> None:
        with SessionLocal() as session:
            _service(session).remover_item(item_id)
            auditar(session, "venda", "REMOVER_ITEM", f"item={item_id}")
            session.commit()

    @requer_permissao("vendas", "editar")
    def aprovar_orcamento(self, venda_id: int):
        with SessionLocal() as session:
            venda = _service(session).aprovar_orcamento(venda_id)
            auditar(session, "venda", "APROVAR", venda.numero, venda.id)
            session.commit()
            return venda

    @requer_permissao("vendas", "editar")
    def recusar_orcamento(self, venda_id: int, motivo: str):
        with SessionLocal() as session:
            venda = _service(session).recusar_orcamento(venda_id, motivo)
            auditar(session, "venda", "RECUSAR", f"{venda.numero}: {motivo}", venda.id)
            session.commit()
            return venda

    @requer_permissao("vendas", "editar")
    def finalizar_venda(
        self,
        venda_id: int,
        usuario_id: int | None = None,
        data_vencimento=None,
        parcelas: int = 1,
        forma_pagamento: str | None = None,
    ):
        with SessionLocal() as session:
            venda = _service(session).finalizar_venda(
                venda_id, usuario_atual(usuario_id), data_vencimento, parcelas, forma_pagamento
            )
            auditar(session, "venda", "FINALIZAR", f"{venda.numero} total={venda.valor_total}", venda.id)
            session.commit()
            return venda

    @requer_permissao("vendas", "excluir")
    def cancelar_venda(self, venda_id: int, motivo: str, usuario_id: int | None = None):
        with SessionLocal() as session:
            venda = _service(session).cancelar_venda(venda_id, motivo, usuario_atual(usuario_id))
            auditar(session, "venda", "CANCELAR", f"{venda.numero}: {motivo}", venda.id)
            session.commit()
            return venda
