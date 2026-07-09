import pytest

from app.models.cliente import Cliente
from app.models.produto import Produto
from app.models.veiculo import Veiculo
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.os_repository import ItemOSRepository, OrdemServicoRepository
from app.repositories.venda_repository import FinanceiroLancamentoRepository
from app.services.estoque_service import EstoqueService
from app.services.os_service import OrdemServicoService


def _service(session):
    estoque_service = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))
    return OrdemServicoService(
        OrdemServicoRepository(session),
        ItemOSRepository(session),
        FinanceiroLancamentoRepository(session),
        estoque_service,
    ), estoque_service


def _cliente_veiculo_produto(session):
    cliente = Cliente(nome="Cliente OS", tipo_pessoa="PF", cpf_cnpj="OS001", ativo=True)
    veiculo = Veiculo(cliente=cliente, placa="ABC1234", marca="VW", modelo="Gol")
    produto = Produto(codigo="OS-P001", descricao="Filtro OS", unidade="UN")
    session.add_all([cliente, veiculo, produto])
    session.flush()
    return cliente, veiculo, produto


def test_finalizar_os_baixa_peca_e_gera_receber(session):
    cliente, veiculo, produto = _cliente_veiculo_produto(session)
    service, estoque_service = _service(session)
    estoque_service.movimentar(produto.id, "ENTRADA", 4, "TESTE")
    ordem = service.abrir_os(
        {
            "cliente_id": cliente.id,
            "veiculo_id": veiculo.id,
            "numero": "OS001",
            "defeito_relatado": "Barulho",
            "diagnostico": "Trocar filtro",
        }
    )
    service.adicionar_item(ordem.id, "PECA", produto.id, "Filtro", 1, 80)
    service.adicionar_item(ordem.id, "SERVICO", "", "Mao de obra", 1, 120)

    service.finalizar_os(ordem.id)

    estoque = EstoqueRepository(session).buscar_por_produto(produto.id)
    lancamentos = FinanceiroLancamentoRepository(session).listar()
    assert ordem.status == "FINALIZADA"
    assert ordem.valor_total == 200
    assert estoque.quantidade_atual == 3
    assert lancamentos[0].origem == "OS"
    assert lancamentos[0].tipo == "RECEBER"
    assert lancamentos[0].valor == 200


def test_finalizar_os_sem_estoque_falha(session):
    cliente, veiculo, produto = _cliente_veiculo_produto(session)
    service, _estoque_service = _service(session)
    ordem = service.abrir_os(
        {
            "cliente_id": cliente.id,
            "veiculo_id": veiculo.id,
            "numero": "OS002",
            "defeito_relatado": "Falha",
            "diagnostico": "Trocar bateria",
        }
    )
    service.adicionar_item(ordem.id, "PECA", produto.id, "Bateria", 1, 300)

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        service.finalizar_os(ordem.id)
