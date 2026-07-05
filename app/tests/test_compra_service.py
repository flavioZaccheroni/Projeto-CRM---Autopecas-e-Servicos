from app.models.fornecedor import Fornecedor
from app.models.produto import Produto
from app.repositories.compra_repository import CompraRepository, ItemCompraRepository
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.services.compra_service import CompraService
from app.services.estoque_service import EstoqueService


def test_receber_compra_gera_entrada_no_estoque(session):
    fornecedor = Fornecedor(razao_social="Fornecedor A", cnpj="111", ativo=True)
    produto = Produto(codigo="P003", descricao="Pastilha", unidade="UN")
    session.add_all([fornecedor, produto])
    session.flush()
    estoque_service = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))
    compra_service = CompraService(CompraRepository(session), ItemCompraRepository(session), estoque_service)
    compra = compra_service.criar_compra({"fornecedor_id": fornecedor.id, "numero": "C001"})
    compra_service.adicionar_item(compra.id, produto.id, 3, 10)

    compra_service.receber_compra(compra.id)

    estoque = EstoqueRepository(session).buscar_por_produto(produto.id)
    assert compra.status == "RECEBIDA"
    assert estoque.quantidade_atual == 3
