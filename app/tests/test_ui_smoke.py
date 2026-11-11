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
