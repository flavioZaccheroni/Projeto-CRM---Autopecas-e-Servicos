"""Sprint 2: numeracao, parcelamento, cancelamento/estorno, orcamento, itens, compra->pagar, impressao de OS."""

from datetime import date
from decimal import Decimal

import pytest

from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.produto import Produto
from app.models.veiculo import Veiculo
from app.repositories.compra_repository import CompraRepository, ItemCompraRepository
from app.repositories.estoque_repository import EstoqueRepository, MovimentacaoEstoqueRepository
from app.repositories.financeiro_repository import CaixaMovimentacaoRepository, FinanceiroRepository
from app.repositories.os_repository import ItemOSRepository, OrdemServicoRepository
from app.repositories.venda_repository import (
    FinanceiroLancamentoRepository,
    ItemVendaRepository,
    VendaRepository,
)
from app.reports.os_pdf import gerar_pdf_os
from app.services.compra_service import CompraService
from app.services.estoque_service import EstoqueService
from app.services.financeiro_service import FinanceiroService
from app.services.numeracao_service import NumeracaoService
from app.services.os_service import OrdemServicoService
from app.services.venda_service import VendaService


@pytest.fixture()
def ctx(session):
    cliente = Cliente(nome="Cliente Teste", tipo_pessoa="PF", cpf_cnpj="52998224725", telefone="11987654321", ativo=True)
    veiculo = Veiculo(cliente=cliente, placa="ABC1D23", marca="VW", modelo="Gol")
    fornecedor = Fornecedor(razao_social="Forn", cnpj="11222333000181", ativo=True)
    produto = Produto(codigo="P1", descricao="Filtro", unidade="UN")
    session.add_all([cliente, veiculo, fornecedor, produto])
    session.flush()
    estoque = EstoqueService(EstoqueRepository(session), MovimentacaoEstoqueRepository(session))
    estoque.movimentar(produto.id, "ENTRADA", 10, "TESTE")
    return type(
        "Ctx",
        (),
        {
            "session": session,
            "cliente": cliente,
            "veiculo": veiculo,
            "fornecedor": fornecedor,
            "produto": produto,
            "estoque": estoque,
            "saldo": lambda self: EstoqueRepository(session).buscar_por_produto(produto.id).quantidade_atual,
            "lancamentos": lambda self: FinanceiroLancamentoRepository(session).listar(),
            "venda": VendaService(
                VendaRepository(session), ItemVendaRepository(session), FinanceiroLancamentoRepository(session), estoque
            ),
            "os": OrdemServicoService(
                OrdemServicoRepository(session), ItemOSRepository(session), FinanceiroLancamentoRepository(session), estoque
            ),
            "compra": CompraService(
                CompraRepository(session), ItemCompraRepository(session), estoque, FinanceiroLancamentoRepository(session)
            ),
            "financeiro": FinanceiroService(FinanceiroRepository(session), CaixaMovimentacaoRepository(session)),
        },
    )()


# -- numeracao ---------------------------------------------------------------------------------
def test_numeracao_sequencial_por_tipo(session):
    numeracao = NumeracaoService(session)
    assert numeracao.proximo("VENDA") == "V000001"
    assert numeracao.proximo("VENDA") == "V000002"
    assert numeracao.proximo("OS") == "OS000001"
    assert numeracao.proximo("COMPRA") == "C000001"
    with pytest.raises(ValueError):
        numeracao.proximo("OUTRO")


def test_numero_e_gerado_quando_nao_informado(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ordem = ctx.os.abrir_os({"cliente_id": ctx.cliente.id, "veiculo_id": ctx.veiculo.id})
    compra = ctx.compra.criar_compra({"fornecedor_id": ctx.fornecedor.id})
    assert (venda.numero, ordem.numero, compra.numero) == ("V000001", "OS000001", "C000001")


# -- venda: parcelamento, orcamento, itens, cancelamento ---------------------------------------
def test_finalizar_venda_parcelada_gera_n_lancamentos(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 1, 100)

    ctx.venda.finalizar_venda(venda.id, data_vencimento="2026-03-01", parcelas=3, forma_pagamento="boleto")

    lancamentos = ctx.lancamentos()
    assert [l.valor for l in lancamentos] == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert lancamentos[0].data_vencimento == date(2026, 3, 1)
    assert lancamentos[0].descricao.endswith("(1/3)")
    assert (venda.forma_pagamento, venda.parcelas) == ("BOLETO", 3)


def test_forma_pagamento_invalida(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 1, 10)
    with pytest.raises(ValueError, match="Forma de pagamento"):
        ctx.venda.finalizar_venda(venda.id, forma_pagamento="cheque_voador")


def test_orcamento_aprovado_vira_venda_e_recusado_nao_finaliza(ctx):
    vazio = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    with pytest.raises(ValueError, match="pelo menos um item"):
        ctx.venda.aprovar_orcamento(vazio.id)

    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 2, 10)
    ctx.venda.aprovar_orcamento(venda.id)
    assert venda.status == "APROVADO"
    ctx.venda.finalizar_venda(venda.id)
    assert venda.status == "FINALIZADA"

    recusado = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(recusado.id, ctx.produto.id, 1, 10)
    ctx.venda.recusar_orcamento(recusado.id, "Cliente achou caro")
    assert recusado.status == "RECUSADO"
    with pytest.raises(ValueError, match="nao pode ser finalizada"):
        ctx.venda.finalizar_venda(recusado.id)


def test_editar_e_remover_item_recalcula_total(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    item1 = ctx.venda.adicionar_item(venda.id, ctx.produto.id, 1, 100)
    item2 = ctx.venda.adicionar_item(venda.id, ctx.produto.id, 2, 50)
    assert venda.valor_total == 200

    ctx.venda.atualizar_item(item1.id, "3", "10,50")
    assert venda.valor_total == Decimal("131.50")

    ctx.venda.remover_item(item2.id)
    assert venda.valor_total == Decimal("31.50")
    assert len(venda.itens) == 1


def test_nao_edita_itens_de_venda_finalizada(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    item = ctx.venda.adicionar_item(venda.id, ctx.produto.id, 1, 10)
    ctx.venda.finalizar_venda(venda.id)
    with pytest.raises(ValueError, match="nao permite alterar itens"):
        ctx.venda.remover_item(item.id)


def test_cancelar_venda_finalizada_devolve_estoque_e_cancela_titulos(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 4, 25)
    ctx.venda.finalizar_venda(venda.id, parcelas=2)
    assert ctx.saldo() == 6

    with pytest.raises(ValueError, match="Motivo"):
        ctx.venda.cancelar_venda(venda.id, "  ")
    ctx.venda.cancelar_venda(venda.id, "Cliente desistiu")

    assert venda.status == "CANCELADA"
    assert venda.motivo_cancelamento == "Cliente desistiu"
    assert ctx.saldo() == 10
    assert {l.status for l in ctx.lancamentos()} == {"CANCELADO"}
    with pytest.raises(ValueError, match="ja cancelada"):
        ctx.venda.cancelar_venda(venda.id, "de novo")


def test_cancelar_venda_com_titulo_pago_estorna_o_caixa(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 1, 80)
    ctx.venda.finalizar_venda(venda.id)
    ctx.financeiro.baixar_lancamento(ctx.lancamentos()[0].id, "PIX")
    assert ctx.financeiro.saldo_caixa() == 80

    ctx.venda.cancelar_venda(venda.id, "Devolucao")

    assert ctx.lancamentos()[0].status == "ESTORNADO"
    assert ctx.financeiro.saldo_caixa() == 0


def test_cancelar_orcamento_nao_mexe_em_estoque(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 3, 10)
    ctx.venda.cancelar_venda(venda.id, "Engano")
    assert ctx.saldo() == 10
    assert ctx.lancamentos() == []


def test_lancamento_cancelado_nao_pode_ser_baixado(ctx):
    venda = ctx.venda.criar_venda({"cliente_id": ctx.cliente.id})
    ctx.venda.adicionar_item(venda.id, ctx.produto.id, 1, 10)
    ctx.venda.finalizar_venda(venda.id)
    ctx.venda.cancelar_venda(venda.id, "Erro")
    with pytest.raises(ValueError, match="cancelado nao pode ser baixado"):
        ctx.financeiro.baixar_lancamento(ctx.lancamentos()[0].id, "PIX")


# -- compra ------------------------------------------------------------------------------------
def test_receber_compra_gera_conta_a_pagar_parcelada(ctx):
    compra = ctx.compra.criar_compra({"fornecedor_id": ctx.fornecedor.id})
    ctx.compra.adicionar_item(compra.id, ctx.produto.id, 5, 20)

    ctx.compra.receber_compra(compra.id, data_vencimento="2026-05-10", parcelas=2)

    lancamentos = ctx.lancamentos()
    assert ctx.saldo() == 15
    assert [(l.tipo, l.origem, l.valor, l.fornecedor_id) for l in lancamentos] == [
        ("PAGAR", "COMPRA", Decimal("50.00"), ctx.fornecedor.id),
        ("PAGAR", "COMPRA", Decimal("50.00"), ctx.fornecedor.id),
    ]


def test_cancelar_compra_recebida_devolve_estoque_e_cancela_pagar(ctx):
    compra = ctx.compra.criar_compra({"fornecedor_id": ctx.fornecedor.id})
    ctx.compra.adicionar_item(compra.id, ctx.produto.id, 5, 20)
    ctx.compra.receber_compra(compra.id)

    ctx.compra.cancelar_compra(compra.id, "Pedido duplicado")

    assert compra.status == "CANCELADA"
    assert ctx.saldo() == 10
    assert ctx.lancamentos()[0].status == "CANCELADO"


def test_cancelar_compra_falha_se_mercadoria_ja_foi_vendida(ctx):
    compra = ctx.compra.criar_compra({"fornecedor_id": ctx.fornecedor.id})
    ctx.compra.adicionar_item(compra.id, ctx.produto.id, 5, 20)
    ctx.compra.receber_compra(compra.id)
    ctx.estoque.movimentar(ctx.produto.id, "SAIDA", 12, "VENDA:X")  # sobram 3 de 15

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        ctx.compra.cancelar_compra(compra.id, "Erro")


def test_compra_recebida_nao_aceita_mais_itens(ctx):
    compra = ctx.compra.criar_compra({"fornecedor_id": ctx.fornecedor.id})
    ctx.compra.adicionar_item(compra.id, ctx.produto.id, 1, 10)
    ctx.compra.receber_compra(compra.id)
    with pytest.raises(ValueError, match="nao permite alterar itens"):
        ctx.compra.adicionar_item(compra.id, ctx.produto.id, 1, 10)


# -- ordem de servico --------------------------------------------------------------------------
def test_cancelar_os_finalizada_devolve_pecas(ctx):
    ordem = ctx.os.abrir_os({"cliente_id": ctx.cliente.id, "veiculo_id": ctx.veiculo.id})
    ctx.os.adicionar_item(ordem.id, "PECA", ctx.produto.id, "Filtro", 2, 40)
    ctx.os.adicionar_item(ordem.id, "SERVICO", "", "Mao de obra", 1, 100)
    ctx.os.finalizar_os(ordem.id, parcelas=2, forma_pagamento="PIX")
    assert ctx.saldo() == 8
    assert sum(l.valor for l in ctx.lancamentos()) == 180

    ctx.os.cancelar_os(ordem.id, "Cliente nao aprovou")

    assert ordem.status == "CANCELADA"
    assert ctx.saldo() == 10
    assert {l.status for l in ctx.lancamentos()} == {"CANCELADO"}


def test_os_editar_remover_item(ctx):
    ordem = ctx.os.abrir_os({"cliente_id": ctx.cliente.id, "veiculo_id": ctx.veiculo.id})
    peca = ctx.os.adicionar_item(ordem.id, "PECA", ctx.produto.id, "Filtro", 1, 50)
    servico = ctx.os.adicionar_item(ordem.id, "SERVICO", "", "Mao de obra", 1, 100)
    ctx.os.atualizar_item(peca.id, 2, 50)
    assert ordem.valor_total == 200
    ctx.os.remover_item(servico.id)
    assert ordem.valor_total == 100


def test_pdf_da_os_e_gerado(ctx, tmp_path):
    ordem = ctx.os.abrir_os(
        {"cliente_id": ctx.cliente.id, "veiculo_id": ctx.veiculo.id, "defeito_relatado": "Barulho"}
    )
    ctx.os.adicionar_item(ordem.id, "PECA", ctx.produto.id, "Filtro de oleo", 1, 55.5)
    ctx.os.adicionar_item(ordem.id, "SERVICO", "", "Troca", 1, 30)

    pdf = gerar_pdf_os(ordem, tmp_path, "Oficina Teste")

    conteudo = pdf.read_bytes()
    assert conteudo.startswith(b"%PDF")
    assert b"ORDEM DE SERVICO OS000001" in conteudo
    assert b"Filtro de oleo" in conteudo
    assert b"Oficina Teste" in conteudo
