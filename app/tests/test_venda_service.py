import pytest

from app.models.cliente import Cliente
from app.models.produto import Produto
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.venda_repository import (
    FinanceiroLancamentoRepository,
    ItemVendaRepository,
    VendaRepository,
)
from app.services.estoque_service import EstoqueService
from app.services.venda_service import VendaService


def test_finalizar_venda_baixa_estoque_e_gera_receber(session):
    cliente = Cliente(nome="Cliente Venda", tipo_pessoa="PF", cpf_cnpj="999", ativo=True)
    produto = Produto(codigo="VENDA-001", descricao="Correia", unidade="UN")
    session.add_all([cliente, produto])
    session.flush()
    estoque_service = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))
    venda_service = VendaService(
        VendaRepository(session),
        ItemVendaRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    )
    estoque_service.movimentar(produto.id, "ENTRADA", 5, "TESTE")
    venda = venda_service.criar_venda({"cliente_id": cliente.id, "numero": "V001"})
    venda_service.adicionar_item(venda.id, produto.id, 2, 50)

    venda_service.finalizar_venda(venda.id)

    estoque = EstoqueRepository(session).buscar_por_produto(produto.id)
    lancamentos = FinanceiroLancamentoRepository(session).listar()
    assert venda.status == "FINALIZADA"
    assert estoque.quantidade_atual == 3
    assert lancamentos[0].tipo == "RECEBER"
    assert lancamentos[0].valor == 100


def test_finalizar_venda_sem_estoque_falha(session):
    cliente = Cliente(nome="Cliente Sem Estoque", tipo_pessoa="PF", cpf_cnpj="998", ativo=True)
    produto = Produto(codigo="VENDA-002", descricao="Bateria", unidade="UN")
    session.add_all([cliente, produto])
    session.flush()
    estoque_service = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))
    venda_service = VendaService(
        VendaRepository(session),
        ItemVendaRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    )
    venda = venda_service.criar_venda({"cliente_id": cliente.id, "numero": "V002"})
    venda_service.adicionar_item(venda.id, produto.id, 1, 300)

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        venda_service.finalizar_venda(venda.id)
