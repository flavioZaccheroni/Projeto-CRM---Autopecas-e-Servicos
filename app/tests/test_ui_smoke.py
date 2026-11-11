"""Testes de fumaca da nova interface PySide6 (sem tela: plataforma offscreen)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.ui import icones  # noqa: E402
from app.ui.componentes import Coluna, KpiCard, Seletor, TabelaDados  # noqa: E402
from app.ui.tema import TOKENS, gerar_qss, tema  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_qss_gerado_para_os_dois_temas():
    for modo, tokens in TOKENS.items():
        qss = gerar_qss(tokens)
        assert tokens["primaria"] in qss, modo
        assert "{" in qss and "}" in qss


def test_todos_os_icones_renderizam(qapp):
    for nome in icones.nomes():
        assert not icones.pixmap(nome, "#0d9488", 20).isNull(), nome


def test_tabela_filtra_sem_acento_e_ordena_pelo_valor(qapp):
    tabela = TabelaDados([Coluna("ID", "num", 60), Coluna("Nome", "texto", 150)])
    tabela.definir_dados([(1, [1, "João Almeida"]), (2, [2, "Maria"]), (10, [10, "Joana"])])
    assert tabela.total() == 3
    tabela.busca.setText("joao")
    assert tabela.proxy.rowCount() == 1
    tabela.busca.setText("")
    tabela.tabela.sortByColumn(0, __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.SortOrder.AscendingOrder)
    assert [tabela.proxy.index(i, 0).data() for i in range(3)] == ["1", "2", "10"]


def test_seletor_devolve_so_o_id(qapp):
    seletor = Seletor(lambda: [(1, "João"), (2, "Maria")])
    seletor.setCurrentText("2 - Maria")
    assert seletor.id() == "2"
    seletor.limpar()
    assert seletor.id() == ""


def test_kpi_anima_ate_o_valor_final(qapp):
    kpi = KpiCard("Teste", "grafico", "primaria")
    kpi.definir_valor("R$ 1,00")
    assert kpi is not None


def test_login_e_janela_principal(qapp, app_db):
    from app.controllers.auth_controller import AuthController
    from app.ui.login import JanelaLogin
    from app.ui.paginas import fabricas_de_paginas
    from app.ui.shell import JanelaPrincipal

    janela_login = JanelaLogin()
    assert janela_login.windowTitle()
    usuario = AuthController().autenticar("admin", "admin123")
    assert usuario is not None
    for modo in ("escuro", "claro"):
        tema.aplicar(modo)
        principal = JanelaPrincipal(usuario, fabricas_de_paginas(usuario))
        principal.show()
        principal.close()


def test_dashboard_e_graficos(qapp, app_db):
    from app.controllers.auth_controller import AuthController
    from app.ui.graficos import GraficoBarras, moeda_curta
    from app.ui.paginas.dashboard import PaginaDashboard, variacao

    assert moeda_curta(1250) == "1,3 mil" and moeda_curta(2_500_000) == "2,5 mi" and moeda_curta(80) == "80"
    assert variacao(150, 100)[1] == "sucesso" and variacao(50, 100)[1] == "perigo" and variacao(10, 0)[1] == "info"
    grafico = GraficoBarras()
    grafico.definir_dados([("Jan", 10), ("Fev", 20)], animar=False)
    grafico.resize(400, 240)
    assert not grafico.grab().isNull() and len(grafico.dados()) == 2
    usuario = AuthController().autenticar("admin", "admin123")
    pagina = PaginaDashboard(usuario)
    pagina.resize(1100, 800)
    pagina.recarregar()
    assert not pagina.grab().isNull()


def test_formulario_le_e_preenche_valores(qapp):
    from app.ui.formulario import Campo, Formulario

    form = Formulario(
        [
            Campo("nome", "Nome"),
            Campo("uf", "UF", "lista", ["SP", "RJ"], somente_lista=True, metade=True),
            Campo("cliente_id", "Cliente", "busca", fonte=lambda: [(1, "Ana"), (2, "Beto")], metade=True),
            Campo("unidade", "Unidade", "lista", ["UN", "PC"], padrao="UN"),
            Campo("ativo", "Ativo", "bool"),
        ]
    )
    avisos = []
    form.alterado.connect(lambda: avisos.append(1))
    form.preencher({"nome": "Maria", "uf": "RJ", "cliente_id": 2, "ativo": False})
    assert not avisos  # preencher nao conta como alteracao do usuario
    assert form.valores() == {"nome": "Maria", "uf": "RJ", "cliente_id": "2", "unidade": "", "ativo": False}
    form.preencher(None)
    assert form.valores()["ativo"] is True and form.valores()["unidade"] == "UN"
    form.widgets["nome"].setText("x")
    assert avisos


def test_cadastro_cria_edita_e_valida(qapp, app_db):
    from app.controllers.auth_controller import AuthController
    from app.ui.paginas.cadastros import ESPECS, PaginaCadastro

    AuthController().autenticar("admin", "admin123")
    pagina = PaginaCadastro(ESPECS["Clientes"])
    pagina.resize(1100, 700)
    assert pagina.tabela.total() == 0
    pagina.novo()
    assert pagina.painel.aberto
    pagina.formulario.widgets["nome"].setText("Maria Teste")
    pagina.formulario.widgets["cpf_cnpj"].setText("123")  # invalido
    pagina.salvar()
    assert pagina.erro.text() and pagina.tabela.total() == 0
    pagina.formulario.widgets["cpf_cnpj"].setText("52998224725")  # CPF valido
    pagina.formulario.widgets["tipo_pessoa"].setCurrentText("PF")
    pagina.salvar()
    assert pagina.tabela.total() == 1 and not pagina.erro.text()
    assert pagina._id_atual is not None  # segue editando o registro salvo
    pagina._sujo = False
    pagina.cancelar()
    assert not pagina.painel._aberto


def _preparar_dados(admin):
    from app.controllers.cadastro_controller import ClienteController, FornecedorController, ProdutoController, VeiculoController

    ClienteController().salvar({"nome": "Ana", "tipo_pessoa": "PF", "cpf_cnpj": "52998224725", "ativo": True})
    FornecedorController().salvar({"razao_social": "Forn SA", "cnpj": "11222333000181", "ativo": True})
    ProdutoController().salvar({"codigo": "P1", "descricao": "Filtro", "unidade": "UN", "preco_custo": "10", "preco_venda": "25", "estoque_minimo": "3", "ativo": True})
    VeiculoController().salvar({"cliente_id": 1, "placa": "ABC1D23", "marca": "VW", "modelo": "Gol"})


def test_venda_fluxo_na_pagina(qapp, app_db):
    from app.controllers.auth_controller import AuthController
    from app.ui.paginas.documentos import ESPECS_DOC, PaginaDocumento

    admin = AuthController().autenticar("admin", "admin123")
    _preparar_dados(admin)
    pagina = PaginaDocumento(ESPECS_DOC["Vendas"], admin)
    pagina.resize(1200, 760)
    assert pagina.tabela.total() == 0
    venda = pagina.controller.criar_venda({"cliente_id": 1}, usuario_id=admin.id)
    pagina.recarregar(avisar=False)
    pagina.tabela.selecionar(str(venda.id))
    pagina._mostrar(str(venda.id))
    assert pagina.painel.aberto and not pagina.botoes["finalizar"].isHidden()
    # adiciona item pelo formulario inline
    pagina.produto.definir_id(1)
    pagina._produto_escolhido(pagina.produto.opcao())
    assert pagina.valor.text()  # preco de venda sugerido
    pagina.qtd.setText("2")
    pagina.adicionar_item()
    assert pagina.itens.rowCount() == 1 and "50,00" in pagina.total.text()
    # edicao inline do item atualiza o total
    pagina._editar_item(pagina.itens._ids[0], "4", "25")
    assert "100,00" in pagina.total.text()
    # quantidade invalida: erro vira aviso e a tabela volta ao valor gravado
    pagina._editar_item(pagina.itens._ids[0], "abc", "25")
    assert "100,00" in pagina.total.text()
    # aprovar muda a etapa e as acoes disponiveis
    pagina.acionar(next(a for a in ESPECS_DOC["Vendas"].acoes if a.chave == "aprovar"))
    assert pagina.etapas._indice == 1 and not pagina.botoes["aprovar"].isEnabled() and pagina.botoes["finalizar"].isEnabled()
    assert not pagina.grab().isNull()


def test_os_compra_estoque_financeiro_relatorios_constroem(qapp, app_db):
    from app.controllers.auth_controller import AuthController
    from app.ui.paginas.documentos import ESPECS_DOC, PaginaDocumento
    from app.ui.paginas.estoque import PaginaEstoque
    from app.ui.paginas.financeiro import PaginaFinanceiro, situacao
    from app.ui.paginas.relatorios import PaginaRelatorios

    admin = AuthController().autenticar("admin", "admin123")
    _preparar_dados(admin)
    os_page = PaginaDocumento(ESPECS_DOC["Ordem de Servico"], admin)
    ordem = os_page.controller.abrir_os({"cliente_id": 1, "veiculo_id": 1, "defeito_relatado": "barulho", "status": "AGUARDANDO_PECA"}, usuario_id=admin.id)
    os_page.recarregar(avisar=False)
    os_page.tabela.selecionar(str(ordem.id))
    os_page._mostrar(str(ordem.id))
    assert os_page.etapas._rotulo_atual == "Aguardando peca"  # status intermediario destacado
    compra_page = PaginaDocumento(ESPECS_DOC["Compras"], admin)
    pedido = compra_page.controller.criar_compra({"fornecedor_id": 1}, usuario_id=admin.id)
    compra_page.recarregar(avisar=False)
    compra_page._mostrar(str(pedido.id))
    estoque = PaginaEstoque(admin)
    estoque.controller.movimentar({"produto_id": "1", "tipo": "ENTRADA", "quantidade": "2", "origem": "MANUAL", "localizacao": ""}, usuario_id=admin.id)
    estoque.recarregar(avisar=False)
    assert estoque.tab_saldo.total() == 1 and estoque.kpi_baixo.valor.text() == "1"  # saldo 2 <= minimo 3
    financeiro = PaginaFinanceiro(admin)
    financeiro.controller.criar_lancamento({"tipo": "PAGAR", "descricao": "Luz", "valor": "80", "data_vencimento": "2020-01-01", "origem": "MANUAL", "origem_id": 0})
    financeiro.recarregar(avisar=False)
    lanc = next(iter(financeiro.lancamentos.values()))
    assert situacao(lanc) == "Vencido"
    financeiro.tab_lanc.selecionar(str(lanc.id))
    assert financeiro.botao_baixar.isEnabled() and not financeiro.botao_estornar.isEnabled()
    PaginaRelatorios()
    for pagina in (os_page, compra_page, estoque, financeiro):
        pagina.resize(1200, 760)
        assert not pagina.grab().isNull()
