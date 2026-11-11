from datetime import date, datetime
from decimal import Decimal

import pytest

from app.models.categoria_produto import CategoriaProduto
from app.models.cliente import Cliente
from app.models.financeiro_lancamento import FinanceiroLancamento
from app.models.ordem_servico import OrdemServico
from app.models.produto import Produto
from app.models.venda import Venda
from app.models.veiculo import Veiculo
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.venda_repository import VendaRepository
from app.services.dashboard_service import DashboardService, inicio_do_mes
from app.services.estoque_service import EstoqueService
from app.services.financeiro_service import FinanceiroService
from app.services.lookup_service import LookupService
from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository

HOJE = date(2026, 11, 15)


@pytest.fixture()
def base(session):
    cliente = Cliente(nome="Maria", tipo_pessoa="PF", cpf_cnpj="52998224725", ativo=True)
    veiculo = Veiculo(cliente=cliente, placa="ABC1D23", marca="VW", modelo="Gol")
    session.add_all([cliente, veiculo])
    session.flush()
    return cliente, veiculo


def test_inicio_do_mes_desloca_entre_anos():
    assert inicio_do_mes(date(2026, 1, 20)) == date(2026, 1, 1)
    assert inicio_do_mes(date(2026, 1, 20), -1) == date(2025, 12, 1)
    assert inicio_do_mes(date(2026, 11, 20), 2) == date(2027, 1, 1)


def test_faturamento_do_mes_soma_vendas_e_os_finalizadas(session, base):
    cliente, veiculo = base
    session.add_all(
        [
            Venda(cliente_id=cliente.id, numero="V1", status="FINALIZADA", valor_total=Decimal("100"), data_venda=datetime(2026, 11, 3)),
            Venda(cliente_id=cliente.id, numero="V2", status="FINALIZADA", valor_total=Decimal("50.50"), data_venda=datetime(2026, 11, 30, 23, 59)),
            Venda(cliente_id=cliente.id, numero="V3", status="CANCELADA", valor_total=Decimal("999"), data_venda=datetime(2026, 11, 4)),
            Venda(cliente_id=cliente.id, numero="V4", status="FINALIZADA", valor_total=Decimal("70"), data_venda=datetime(2026, 10, 31)),
            Venda(cliente_id=cliente.id, numero="V5", status="ORCAMENTO", valor_total=Decimal("10"), data_venda=datetime(2026, 11, 5)),
            OrdemServico(cliente_id=cliente.id, veiculo_id=veiculo.id, numero="OS1", status="FINALIZADA", valor_total=Decimal("200"), data_abertura=datetime(2026, 11, 10)),
            OrdemServico(cliente_id=cliente.id, veiculo_id=veiculo.id, numero="OS2", status="ABERTA", valor_total=Decimal("5"), data_abertura=datetime(2026, 11, 11)),
        ]
    )
    session.flush()

    dados = DashboardService(session).vendas(HOJE)

    assert dados["faturamento_mes"] == Decimal("350.50")
    assert dados["vendas_mes"] == 2
    assert dados["os_finalizadas_mes"] == 1
    assert dados["os_abertas"] == 1
    assert dados["orcamentos_abertos"] == 1
    serie = dict(dados["serie_mensal"])
    assert len(serie) == 6
    assert serie["Nov/26"] == Decimal("350.50")
    assert serie["Out/26"] == Decimal("70")
    assert serie["Jun/26"] == 0


def test_financeiro_separa_vencido_e_a_vencer(session):
    def lanc(tipo, valor, venc, status="ABERTO"):
        return FinanceiroLancamento(tipo=tipo, origem="MANUAL", origem_id=0, descricao=f"{tipo} {venc}", valor=Decimal(valor), data_vencimento=venc, status=status)

    session.add_all(
        [
            lanc("RECEBER", "100", date(2026, 11, 1)),  # vencido
            lanc("RECEBER", "40", date(2026, 11, 20)),  # vence em 5 dias
            lanc("RECEBER", "900", date(2026, 12, 25)),  # longe
            lanc("RECEBER", "77", date(2026, 11, 1), status="PAGO"),  # nao conta
            lanc("PAGAR", "30", date(2026, 11, 14)),  # vencido
            lanc("PAGAR", "20", date(2026, 11, 15)),  # vence hoje
            lanc("PAGAR", "11", date(2026, 11, 1), status="CANCELADO"),
        ]
    )
    session.flush()
    financeiro = FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session))
    lancamento = lanc("RECEBER", "60", date(2026, 11, 16))
    session.add(lancamento)
    session.flush()
    financeiro.baixar_lancamento(lancamento.id, "PIX")

    dados = DashboardService(session).financeiro(HOJE)

    assert dados["receber_vencido"] == 100
    assert dados["pagar_vencido"] == 30
    assert dados["receber_7_dias"] == 40
    assert dados["pagar_7_dias"] == 20
    assert dados["saldo_caixa"] == 60
    proximos = dados["proximos_vencimentos"]
    assert proximos[0][0] == date(2026, 11, 1) and proximos[0][4] is True  # vencido primeiro
    assert all(item[4] is False for item in proximos if item[0] >= HOJE)


def test_estoque_baixo_inclui_produto_sem_saldo_e_ignora_ok(session):
    sem_saldo = Produto(codigo="A", descricao="Sem saldo", unidade="UN", estoque_minimo=Decimal("5"))
    baixo = Produto(codigo="B", descricao="Baixo", unidade="UN", estoque_minimo=Decimal("5"))
    ok = Produto(codigo="C", descricao="Ok", unidade="UN", estoque_minimo=Decimal("5"))
    sem_minimo = Produto(codigo="D", descricao="Sem minimo", unidade="UN", estoque_minimo=Decimal("0"))
    inativo = Produto(codigo="E", descricao="Inativo", unidade="UN", estoque_minimo=Decimal("5"), ativo=False)
    session.add_all([sem_saldo, baixo, ok, sem_minimo, inativo])
    session.flush()
    estoque = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))
    estoque.movimentar(baixo.id, "ENTRADA", 2, "T")
    estoque.movimentar(ok.id, "ENTRADA", 9, "T")

    lista = DashboardService(session).estoque_baixo()

    assert [(codigo, atual) for codigo, _desc, atual, _min in lista] == [("A", 0), ("B", 2)]


def test_lookup_lista_apenas_ativos_e_filtra_veiculos_por_cliente(session, base):
    cliente, veiculo = base
    outro = Cliente(nome="Ana", tipo_pessoa="PF", cpf_cnpj="11144477735", ativo=True)
    inativo = Cliente(nome="Zeca", tipo_pessoa="PF", cpf_cnpj="39053344705", ativo=False)
    session.add_all([outro, inativo, CategoriaProduto(nome="Freios", ativo=True), Produto(codigo="P1", descricao="Pastilha", unidade="UN", preco_venda=Decimal("45.90"))])
    session.flush()
    session.add(Veiculo(cliente_id=outro.id, placa="XYZ9876", modelo="Uno"))
    session.flush()
    lookup = LookupService(session)

    assert [nome for _i, nome, _ in lookup.clientes()] == ["Ana", "Maria"]
    assert lookup.produtos() == [(1, "P1 - Pastilha", "45.90")]
    assert [placa for _i, placa, _ in lookup.veiculos(cliente.id)] == ["ABC1D23 - VW Gol"]
    assert len(lookup.veiculos()) == 2
    assert [nome for _i, nome, _ in lookup.categorias()] == ["Freios"]


def test_listagem_carrega_cliente_para_uso_apos_fechar_sessao(session, base):
    cliente, _ = base
    session.add(Venda(cliente_id=cliente.id, numero="V9", valor_total=Decimal("1")))
    session.flush()
    session.expire_all()

    vendas = VendaRepository(session).listar()
    session.close()  # simula a tela usando o objeto depois que a sessao do controller fechou

    assert vendas[0].cliente.nome == "Maria"
