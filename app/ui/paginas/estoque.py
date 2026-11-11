"""Estoque: saldo atual (com alerta de minimo) e historico de movimentacoes; movimento manual por dialogo."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout

from app.controllers.estoque_controller import EstoqueController
from app.controllers.lookup_controller import LookupController
from app.ui.componentes import Botao, Card, Coluna, KpiCard, TabelaDados
from app.ui.formulario import Campo
from app.ui.operacoes import DialogoFormulario
from app.ui.paginas.base import Pagina
from app.utils.sessao import Sessao

TONS_SITUACAO = {"Abaixo do mínimo": "perigo", "Normal": "sucesso"}
TONS_MOV = {"ENTRADA": "sucesso", "SAIDA": "perigo", "AJUSTE": "aviso"}


def _produto(item) -> str:
    produto = getattr(item, "produto", None)
    return f"{produto.codigo} - {produto.descricao}" if produto else ""


def abaixo_do_minimo(item) -> bool:
    produto = getattr(item, "produto", None)
    minimo = Decimal(str(getattr(produto, "estoque_minimo", 0) or 0))
    return minimo > 0 and Decimal(str(item.quantidade_atual)) <= minimo


class PaginaEstoque(Pagina):
    subtitulo = "Saldo por produto, alertas de mínimo e histórico de movimentações."

    def __init__(self, usuario) -> None:
        super().__init__()
        self.usuario = usuario
        self.controller = EstoqueController()
        self.saldos: dict[str, object] = {}

        linha = QHBoxLayout()
        linha.setSpacing(16)
        self.kpi_produtos = KpiCard("Produtos em estoque", "estoque", "primaria", "Itens com saldo cadastrado")
        self.kpi_baixo = KpiCard("Abaixo do mínimo", "alerta", "perigo", "Clique para ver quais são")
        self.kpi_baixo.tornar_clicavel()
        self.kpi_baixo.clicado.connect(self._ver_baixos)
        self.kpi_mov = KpiCard("Movimentações", "atualizar", "info", "Registradas no histórico")
        for kpi in (self.kpi_produtos, self.kpi_baixo, self.kpi_mov):
            linha.addWidget(kpi, 1)
        self.corpo.addLayout(linha)

        card = Card()
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 8, 16, 16)
        self.abas = QTabWidget()
        self.tab_saldo = TabelaDados(
            [Coluna("ID", "num", 50), Coluna("Produto", "texto", 280), Coluna("Saldo", "num", 90), Coluna("Mínimo", "num", 90), Coluna("Localização", "texto", 120), Coluna("Situação", "emblema", 140, TONS_SITUACAO)],
            vazio_titulo="Sem saldos de estoque",
            vazio_texto="Registre uma entrada para começar o controle de estoque.",
            placeholder="Buscar produto…",
        )
        self.tab_mov = TabelaDados(
            [Coluna("ID", "num", 50), Coluna("Data", "data", 130), Coluna("Produto", "texto", 240), Coluna("Tipo", "emblema", 100, TONS_MOV), Coluna("Origem", "texto", 130), Coluna("Qtd", "num", 80), Coluna("Anterior", "num", 80), Coluna("Posterior", "num", 80)],
            vazio_titulo="Sem movimentações",
            vazio_texto="As entradas, saídas e ajustes aparecem aqui.",
            placeholder="Buscar movimentação…",
        )
        self.botao_mov = Botao("Registrar movimento", "primario", "mais")
        self.botao_mov.clicked.connect(lambda: self.movimentar())
        self.botao_mov.setEnabled(Sessao.pode("estoque", "criar"))
        self.tab_saldo.adicionar_acao(self.botao_mov)
        self.tab_saldo.ativado.connect(lambda iid: self.movimentar(iid))
        self.abas.addTab(self.tab_saldo, "Saldo atual")
        self.abas.addTab(self.tab_mov, "Movimentações")
        v.addWidget(self.abas)
        self.corpo.addWidget(card, 1)
        self.recarregar(avisar=False)

    def focar_busca(self) -> bool:
        return self.abas.currentWidget().focar_busca()

    def _ver_baixos(self) -> None:
        self.abas.setCurrentWidget(self.tab_saldo)
        self.tab_saldo.busca.setText("Abaixo")

    def recarregar(self, avisar: bool = True) -> None:
        try:
            saldos = self.controller.listar()
            movimentos = self.controller.listar_movimentacoes()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.saldos = {str(i.id): i for i in saldos}
        self.tab_saldo.definir_dados(
            [
                (str(i.id), [i.id, _produto(i), i.quantidade_atual, getattr(i.produto, "estoque_minimo", ""), i.localizacao, "Abaixo do mínimo" if abaixo_do_minimo(i) else "Normal"])
                for i in saldos
            ]
        )
        self.tab_mov.definir_dados(
            [(str(i.id), [i.id, i.criado_em, _produto(i), i.tipo, i.origem, i.quantidade, i.saldo_anterior, i.saldo_posterior]) for i in movimentos]
        )
        self.kpi_produtos.definir_valor(str(len(saldos)))
        self.kpi_baixo.definir_valor(str(sum(1 for i in saldos if abaixo_do_minimo(i))))
        self.kpi_mov.definir_valor(str(len(movimentos)))

    def movimentar(self, saldo_id=None) -> None:
        if not Sessao.pode("estoque", "criar"):
            self.avisar("Seu perfil não pode registrar movimentos.", "aviso")
            return
        campos = [
            Campo("produto_id", "Produto", "busca", fonte=lambda: LookupController().produtos(), dica="Buscar produto…"),
            Campo("tipo", "Tipo de movimento", "lista", ["ENTRADA", "SAIDA", "AJUSTE"], somente_lista=True, metade=True),
            Campo("quantidade", "Quantidade", metade=True),
            Campo("origem", "Origem", padrao="MANUAL", metade=True),
            Campo("localizacao", "Localização", metade=True),
        ]
        dlg = DialogoFormulario(self, "Registrar movimento", campos, "Registrar", "ENTRADA soma, SAÍDA subtrai e AJUSTE define o saldo.")
        dlg.formulario.widgets["tipo"].setCurrentText("ENTRADA")
        if saldo_id is not None and str(saldo_id) in self.saldos:
            dlg.formulario.widgets["produto_id"].definir_id(self.saldos[str(saldo_id)].produto_id)
        dados = dlg.exec_dados()
        if dados is None:
            return
        if self.executar(lambda: self.controller.movimentar(dados, usuario_id=self.usuario.id), "Movimento registrado."):
            self.recarregar(avisar=False)
