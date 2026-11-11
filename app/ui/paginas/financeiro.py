"""Financeiro: indicadores, lancamentos (filtros rapidos, baixa, estorno, novo) e caixa."""

from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QTabWidget, QVBoxLayout

from app.controllers.financeiro_controller import FinanceiroController
from app.controllers.lookup_controller import LookupController
from app.ui.componentes import Botao, Card, Coluna, KpiCard, TabelaDados
from app.ui.formulario import Campo
from app.ui.graficos import reais
from app.ui.operacoes import DialogoFormulario, confirmar
from app.ui.paginas.base import Pagina
from app.utils.sessao import Sessao

TONS_STATUS = {"Aberto": "info", "Vencido": "perigo", "Pago": "sucesso", "Estornado": "neutro", "Cancelado": "neutro"}
TONS_TIPO = {"RECEBER": "sucesso", "PAGAR": "perigo"}
TONS_CAIXA = {"ENTRADA": "sucesso", "SAIDA": "perigo", "ESTORNO": "aviso"}
FORMAS = ["DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO", "BOLETO", "TRANSFERENCIA"]
FILTROS = [("Todos", ""), ("A receber", "receber"), ("A pagar", "pagar"), ("Vencidos", "vencido"), ("Abertos", "aberto"), ("Pagos", "pago")]


def situacao(lancamento, hoje: date | None = None) -> str:
    """Status exibido: ABERTO com vencimento passado vira 'Vencido'."""
    hoje = hoje or date.today()
    status = str(lancamento.status)
    vencimento = getattr(lancamento, "data_vencimento", None)
    if status == "ABERTO" and vencimento is not None and vencimento < hoje:
        return "Vencido"
    return status.capitalize()


def _parte(item) -> str:
    if getattr(item, "cliente", None):
        return item.cliente.nome
    if getattr(item, "fornecedor", None):
        return item.fornecedor.razao_social
    return ""


class PaginaFinanceiro(Pagina):
    subtitulo = "Contas a pagar e receber, baixas, estornos e movimento de caixa."

    def __init__(self, usuario) -> None:
        super().__init__()
        self.usuario = usuario
        self.controller = FinanceiroController()
        self.lancamentos: dict[str, object] = {}

        linha = QHBoxLayout()
        linha.setSpacing(16)
        self.kpis: dict[str, KpiCard] = {}
        for chave, titulo, icone, tom in (
            ("aberto_receber", "A receber", "tendencia", "info"),
            ("aberto_pagar", "A pagar", "recibo", "aviso"),
            ("pago_receber", "Recebido", "ok", "sucesso"),
            ("pago_pagar", "Pago", "carteira", "neutro"),
            ("saldo_caixa", "Saldo em caixa", "carteira", "primaria"),
        ):
            kpi = KpiCard(titulo, icone, tom)
            self.kpis[chave] = kpi
            linha.addWidget(kpi, 1)
        self.corpo.addLayout(linha)

        card = Card()
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 8, 16, 16)
        self.abas = QTabWidget()
        self.tab_lanc = TabelaDados(
            [Coluna("ID", "num", 50), Coluna("Tipo", "emblema", 95, TONS_TIPO), Coluna("Origem", "texto", 90), Coluna("Descrição", "texto", 220), Coluna("Cliente / fornecedor", "texto", 160),
             Coluna("Valor", "num", 100), Coluna("Vencimento", "data", 100), Coluna("Pagamento", "data", 100), Coluna("Situação", "emblema", 100, TONS_STATUS)],
            vazio_titulo="Nenhum lançamento",
            vazio_texto="Vendas, OS e compras geram lançamentos automaticamente; você também pode criar manualmente.",
            placeholder="Buscar lançamento…",
        )
        self.tab_caixa = TabelaDados(
            [Coluna("ID", "num", 50), Coluna("Data", "data", 130), Coluna("Tipo", "emblema", 100, TONS_CAIXA), Coluna("Descrição", "texto", 260), Coluna("Valor", "num", 100), Coluna("Forma", "texto", 130)],
            vazio_titulo="Caixa sem movimento",
            vazio_texto="As baixas de lançamentos aparecem aqui.",
            placeholder="Buscar no caixa…",
        )
        # filtros rapidos, antes da barra da tabela
        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.grupo = QButtonGroup(self)
        self.grupo.setExclusive(True)
        for i, (rotulo_filtro, termo) in enumerate(FILTROS):
            b = Botao(rotulo_filtro, "filtro")
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.clicked.connect(lambda _=False, t=termo: self.tab_lanc.busca.setText(t))
            self.grupo.addButton(b)
            chips.addWidget(b)
        self.botao_baixar = Botao("Baixar", "primario", "ok")
        self.botao_baixar.clicked.connect(self.baixar)
        self.botao_estornar = Botao("Estornar", "perigo", "atualizar")
        self.botao_estornar.clicked.connect(self.estornar)
        self.botao_novo = Botao("Novo lançamento", "secundario", "mais")
        self.botao_novo.clicked.connect(self.novo)
        for b in (self.botao_estornar, self.botao_baixar, self.botao_novo):
            self.tab_lanc.adicionar_acao(b)
        self.botao_novo.setEnabled(Sessao.pode("financeiro", "criar"))
        self.tab_lanc.selecionado.connect(self._ao_selecionar)
        chips.addStretch()
        self.tab_lanc.layout().insertLayout(0, chips)
        self.abas.addTab(self.tab_lanc, "Lançamentos")
        self.abas.addTab(self.tab_caixa, "Caixa")
        v.addWidget(self.abas)
        self.corpo.addWidget(card, 1)
        self._ao_selecionar(None)
        self.recarregar(avisar=False)

    def focar_busca(self) -> bool:
        return self.abas.currentWidget().focar_busca()

    def recarregar(self, avisar: bool = True) -> None:
        try:
            resumo = self.controller.resumo_fluxo()
            lancamentos = self.controller.listar_lancamentos()
            caixa = self.controller.listar_caixa()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        for chave, kpi in self.kpis.items():
            valor = float(resumo.get(chave, 0))
            kpi.definir_valor(reais(valor))
            if chave == "saldo_caixa":
                kpi.definir_tom("sucesso" if valor >= 0 else "perigo")
        selecionado = self.tab_lanc.iid_atual()
        self.lancamentos = {str(i.id): i for i in lancamentos}
        self.tab_lanc.definir_dados(
            [(str(i.id), [i.id, i.tipo, i.origem, i.descricao, _parte(i), i.valor, i.data_vencimento, i.data_pagamento, situacao(i)]) for i in lancamentos]
        )
        self.tab_caixa.definir_dados([(str(i.id), [i.id, i.criado_em, i.tipo, i.descricao, i.valor, i.forma_pagamento]) for i in caixa])
        if selecionado:
            self.tab_lanc.selecionar(selecionado)
        self._ao_selecionar(self.tab_lanc.iid_atual())

    def _ao_selecionar(self, iid) -> None:
        item = self.lancamentos.get(str(iid)) if iid is not None else None
        status = str(item.status) if item is not None else ""
        self.botao_baixar.setEnabled(status == "ABERTO" and Sessao.pode("financeiro", "editar"))
        self.botao_estornar.setEnabled(status == "PAGO" and Sessao.pode("financeiro", "excluir"))

    def _selecionado(self):
        iid = self.tab_lanc.iid_atual()
        return self.lancamentos.get(str(iid)) if iid is not None else None

    # ---- acoes
    def baixar(self) -> None:
        item = self._selecionado()
        if item is None:
            return
        campos = [Campo("forma_pagamento", "Forma de pagamento", "lista", FORMAS, somente_lista=True, metade=True), Campo("data_pagamento", "Data do pagamento", "data", metade=True)]
        dlg = DialogoFormulario(self, "Baixar lançamento", campos, "Baixar", f"{item.descricao} — {reais(item.valor)}. O valor entra no caixa.")
        dlg.formulario.widgets["forma_pagamento"].setCurrentText("PIX")
        dados = dlg.exec_dados()
        if dados is None:
            return
        ok = self.executar(
            lambda: self.controller.baixar_lancamento(item.id, dados["forma_pagamento"], usuario_id=self.usuario.id, data_pagamento=dados["data_pagamento"]),
            "Lançamento baixado e caixa movimentado.",
        )
        if ok:
            self.recarregar(avisar=False)

    def estornar(self) -> None:
        item = self._selecionado()
        if item is None:
            return
        if not confirmar(self, "Estornar lançamento", f"Estornar “{item.descricao}” ({reais(item.valor)})? O caixa será ajustado.", "Estornar"):
            return
        if self.executar(lambda: self.controller.estornar_lancamento(item.id, usuario_id=self.usuario.id), "Lançamento estornado."):
            self.recarregar(avisar=False)

    def novo(self) -> None:
        campos = [
            Campo("tipo", "Tipo", "lista", ["RECEBER", "PAGAR"], somente_lista=True, metade=True),
            Campo("valor", "Valor", metade=True),
            Campo("descricao", "Descrição"),
            Campo("data_vencimento", "Vencimento", "data"),
            Campo("cliente_id", "Cliente (opcional)", "busca", fonte=lambda: LookupController().clientes(), dica="Buscar cliente…"),
            Campo("fornecedor_id", "Fornecedor (opcional)", "busca", fonte=lambda: LookupController().fornecedores(), dica="Buscar fornecedor…"),
        ]
        dlg = DialogoFormulario(self, "Novo lançamento", campos, "Criar")
        dlg.formulario.widgets["tipo"].setCurrentText("RECEBER")
        dados = dlg.exec_dados()
        if dados is None:
            return
        dados.update(origem="MANUAL", origem_id=0)
        if self.executar(lambda: self.controller.criar_lancamento(dados), "Lançamento criado."):
            self.recarregar(avisar=False)
