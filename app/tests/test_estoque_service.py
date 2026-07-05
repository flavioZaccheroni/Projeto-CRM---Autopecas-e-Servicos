import pytest

from app.models.produto import Produto
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.services.estoque_service import EstoqueService


def test_estoque_nao_permite_saldo_negativo(session):
    produto = Produto(codigo="P001", descricao="Filtro", unidade="UN")
    session.add(produto)
    session.flush()
    service = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        service.movimentar(produto.id, "SAIDA", 1, "TESTE")


def test_estoque_registra_entrada(session):
    produto = Produto(codigo="P002", descricao="Oleo", unidade="UN")
    session.add(produto)
    session.flush()
    service = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))

    movimento = service.movimentar(produto.id, "ENTRADA", 5, "TESTE")

    assert movimento.saldo_anterior == 0
    assert movimento.saldo_posterior == 5
