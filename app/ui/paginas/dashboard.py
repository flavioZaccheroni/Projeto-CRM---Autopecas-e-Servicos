"""Dashboard: KPIs com variacao, grafico de faturamento, alertas clicaveis e listas de estoque/vencimentos."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.controllers.dashboard_controller import DashboardController
from app.ui import icones
from app.ui.componentes import Card, Coluna, EstadoVazio, KpiCard, TabelaDados, rotulo
from app.ui.graficos import BarraComparativa, GraficoBarras, reais
from app.ui.paginas.base import Pagina
from app.ui.tema import ao_mudar_tema, cor_do_tom, tema

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def variacao(atual: float, anterior: float) -> tuple[str, str]:
    """Texto e tom da variacao percentual entre dois periodos."""
    if anterior <= 0:
        return ("Sem base de comparação no mês anterior", "info") if atual <= 0 else ("Primeiro mês com faturamento", "info")
    delta = (atual - anterior) / anterior * 100
    seta = "↑" if delta >= 0 else "↓"
    return f"{seta} {abs(delta):.1f}% sobre o mês anterior".replace(".", ","), "sucesso" if delta >= 0 else "perigo"


class ItemAlerta(QPushButton):
    """Linha clicavel de alerta: icone colorido + mensagem; leva para a tela relacionada."""

    def __init__(self, texto: str, tom: str, icone: str, destino: str) -> None:
        super().__init__()
        self.destino, self._tom, self._icone = destino, tom, icone
        self.setProperty("variante", "fantasma")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        linha = QHBoxLayout(self)
        linha.setContentsMargins(10, 0, 10, 0)
        linha.setSpacing(10)
        self._figura = rotulo("")
        self._figura.setFixedSize(28, 28)
        self._figura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._figura.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._texto = rotulo(texto, "rotulo")
        self._texto.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        seta = rotulo("›", "mudo")
        seta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        linha.addWidget(self._figura)
        linha.addWidget(self._texto, 1)
        linha.addWidget(seta)
        ao_mudar_tema(self, self._pintar)
        self._pintar()

    def _pintar(self) -> None:
        forte, suave = cor_do_tom(tema.t, self._tom)
        self._figura.setStyleSheet(f"background: {suave}; border-radius: 8px;")
        self._figura.setPixmap(icones.pixmap(self._icone, forte, 16))


class PaginaDashboard(Pagina):
    def __init__(self, usuario) -> None:
        super().__init__()
        self.usuario = usuario
        self.controller = DashboardController()
        hoje = date.today()
        self.subtitulo = f"{DIAS[hoje.weekday()].capitalize()}, {hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}  ·  Perfil: {usuario.perfil.nome}"
        self.corpo.setContentsMargins(0, 0, 0, 0)
        self._rolagem = QScrollArea()
        self._rolagem.setWidgetResizable(True)
        self._rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        self.corpo.addWidget(self._rolagem)
        self._kpis: list[tuple[KpiCard, float, object]] = []
        self._primeira = True
        self.recarregar(animar=False)

    # ---- carga
    def ao_abrir(self) -> None:
        if not self._primeira:
            self.recarregar(animar=True)
        self._primeira = False
        self._animar()

    def recarregar(self, animar: bool = True) -> None:
        try:
            dados = self.controller.resumo()
        except Exception as exc:  # noqa: BLE001 - mostra qualquer falha de carga ao usuario
            self.avisar(f"Não foi possível carregar o painel: {exc}", "perigo")
            return
        self._construir(dados)
        if animar:
            self._animar()

    def _animar(self) -> None:
        for kpi, valor, formato in self._kpis:
            kpi.animar_para(valor, formato)
        if getattr(self, "grafico", None) is not None:
            self.grafico.definir_dados(self.grafico.dados())

    # ---- construcao
    def _construir(self, dados: dict) -> None:
        vendas, financeiro, estoque = dados["vendas"], dados["financeiro"], dados["estoque_baixo"]
        conteudo = QWidget()
        pilha = QVBoxLayout(conteudo)
        pilha.setContentsMargins(28, 24, 28, 28)
        pilha.setSpacing(18)
        self._kpis = []
        self.grafico = None
        if vendas is None and financeiro is None and estoque is None:
            pilha.addWidget(EstadoVazio("Nenhum indicador liberado", "Seu perfil não tem indicadores no painel. Use o menu lateral para acessar seus módulos.", "escudo"))
            self._rolagem.setWidget(conteudo)
            return

        if vendas is not None:
            serie = vendas["serie_mensal"]
            atual = float(serie[-1][1]) if serie else 0.0
            anterior = float(serie[-2][1]) if len(serie) > 1 else 0.0
            nota, tom_delta = variacao(atual, anterior)
            pilha.addLayout(
                self._linha(
                    [
                        self._kpi("Faturamento do mês", "tendencia", "primaria", f"{nota}\n{vendas['vendas_mes']} venda(s) + {vendas['os_finalizadas_mes']} OS", float(vendas["faturamento_mes"]), reais, None, tom_delta),
                        self._kpi("OS em aberto", "chave", "info", "Ordens de serviço em andamento", float(vendas["os_abertas"]), lambda v: f"{v:.0f}", "Ordem de Servico"),
                        self._kpi("Orçamentos em aberto", "documento", "aviso", "Aguardando aprovação ou venda", float(vendas["orcamentos_abertos"]), lambda v: f"{v:.0f}", "Vendas"),
                    ]
                )
            )
        if financeiro is not None:
            vencido_r, vencido_p = float(financeiro["receber_vencido"]), float(financeiro["pagar_vencido"])
            saldo = float(financeiro["saldo_caixa"])
            pilha.addLayout(
                self._linha(
                    [
                        self._kpi("Saldo em caixa", "carteira", "sucesso" if saldo >= 0 else "perigo", "Entradas menos saídas realizadas", saldo, reais, "Financeiro"),
                        self._kpi("A receber vencido", "alerta", "perigo" if vencido_r else "neutro", "Títulos em atraso" if vencido_r else "Nada em atraso", vencido_r, reais, "Financeiro"),
                        self._kpi("A pagar vencido", "alerta", "perigo" if vencido_p else "neutro", "Contas em atraso" if vencido_p else "Nada em atraso", vencido_p, reais, "Financeiro"),
                    ]
                )
            )

        meio = QHBoxLayout()
        meio.setSpacing(16)
        if vendas is not None:
            meio.addWidget(self._cartao_grafico(vendas["serie_mensal"]), 3)
        lateral = QVBoxLayout()
        lateral.setSpacing(16)
        lateral.addWidget(self._cartao_alertas(vendas, financeiro, estoque))
        if financeiro is not None:
            lateral.addWidget(self._cartao_fluxo(financeiro))
        lateral.addStretch()
        meio.addLayout(lateral, 2)
        pilha.addLayout(meio)

        listas = QGridLayout()
        listas.setSpacing(16)
        coluna = 0
        if estoque is not None:
            listas.addWidget(self._cartao_estoque(estoque), 0, coluna)
            coluna += 1
        if financeiro is not None:
            listas.addWidget(self._cartao_vencimentos(financeiro["proximos_vencimentos"]), 0, coluna)
        listas.setColumnStretch(0, 2)
        listas.setColumnStretch(1, 3)
        pilha.addLayout(listas)
        pilha.addStretch()
        self._rolagem.setWidget(conteudo)

    def _kpi(self, titulo, icone, tom, nota, valor, formato, destino, tom_nota: str | None = None) -> KpiCard:
        kpi = KpiCard(titulo, icone, tom, nota)
        if tom_nota:
            kpi.nota.setStyleSheet(f"color: {cor_do_tom(tema.t, tom_nota)[0]};")
        kpi.definir_valor(formato(valor))
        if destino:
            kpi.tornar_clicavel()
            kpi.setToolTip(f"Abrir {destino}")
            kpi.clicado.connect(lambda d=destino: self.ir_para(d))
        self._kpis.append((kpi, valor, formato))
        return kpi

    @staticmethod
    def _linha(kpis: list[KpiCard]) -> QHBoxLayout:
        linha = QHBoxLayout()
        linha.setSpacing(16)
        for kpi in kpis:
            linha.addWidget(kpi, 1)
        return linha

    def _cartao(self, titulo: str, descricao: str = "") -> tuple[Card, QVBoxLayout]:
        card = Card()
        corpo = QVBoxLayout(card)
        corpo.setContentsMargins(20, 18, 20, 18)
        corpo.setSpacing(10)
        corpo.addWidget(rotulo(titulo, "secao"))
        if descricao:
            corpo.addWidget(rotulo(descricao, "mudo", quebra=True))
        return card, corpo

    def _cartao_grafico(self, serie) -> Card:
        card, corpo = self._cartao("Faturamento — últimos 6 meses", "Passe o mouse para ver o valor; clique em uma barra para abrir Relatórios.")
        self.grafico = GraficoBarras()
        self.grafico.definir_dados([(r, float(v)) for r, v in serie], animar=False)
        self.grafico.clicada.connect(lambda _i: self.ir_para("Relatorios"))
        self.grafico.setMinimumHeight(260)
        corpo.addWidget(self.grafico, 1)
        return card

    def _cartao_alertas(self, vendas, financeiro, estoque) -> Card:
        card, corpo = self._cartao("Atenção", "Clique para ir direto ao assunto.")
        itens: list[tuple[str, str, str, str]] = []
        if estoque:
            itens.append((f"{len(estoque)} produto(s) com estoque no mínimo ou abaixo", "aviso", "estoque", "Estoque"))
        if financeiro is not None:
            if financeiro["receber_vencido"]:
                itens.append((f"Recebimentos em atraso: {reais(financeiro['receber_vencido'])}", "perigo", "alerta", "Financeiro"))
            if financeiro["pagar_vencido"]:
                itens.append((f"Contas a pagar em atraso: {reais(financeiro['pagar_vencido'])}", "perigo", "alerta", "Financeiro"))
        if vendas is not None and vendas["orcamentos_abertos"]:
            itens.append((f"{vendas['orcamentos_abertos']} orçamento(s) aguardando aprovação", "info", "documento", "Vendas"))
        if not itens:
            corpo.addWidget(EstadoVazio("Tudo em dia", "Nenhum alerta no momento.", "ok"))
            return card
        for texto, tom, icone, destino in itens:
            botao = ItemAlerta(texto, tom, icone, destino)
            botao.clicked.connect(lambda _=False, d=destino: self.ir_para(d))
            corpo.addWidget(botao)
        return card

    def _cartao_fluxo(self, financeiro) -> Card:
        card, corpo = self._cartao("Próximos 7 dias", "Entradas e saídas previstas.")
        barras = BarraComparativa()
        barras.definir([("A receber", float(financeiro["receber_7_dias"]), "sucesso"), ("A pagar", float(financeiro["pagar_7_dias"]), "perigo")])
        corpo.addWidget(barras)
        return card

    def _cartao_estoque(self, linhas) -> Card:
        card, corpo = self._cartao("Estoque abaixo do mínimo", "Dê dois cliques em um produto para abrir o Estoque.")
        tabela = TabelaDados(
            [Coluna("Código", "texto", 70), Coluna("Descrição", "texto", 140), Coluna("Atual", "num", 55), Coluna("Mínimo", "num", 62)],
            vazio_titulo="Tudo certo",
            vazio_texto="Nenhum produto abaixo do mínimo.",
            placeholder="Buscar produto…",
        )
        tabela.definir_dados([(i, list(linha)) for i, linha in enumerate(linhas)])
        tabela.setMinimumHeight(250)
        tabela.ativado.connect(lambda _iid: self.ir_para("Estoque"))
        corpo.addWidget(tabela)
        return card

    def _cartao_vencimentos(self, linhas) -> Card:
        card, corpo = self._cartao("Próximos vencimentos", "Dê dois cliques para abrir o Financeiro.")
        tons = {"Vencido": "perigo", "No prazo": "neutro"}
        tabela = TabelaDados(
            [Coluna("Vencimento", "data", 95), Coluna("Tipo", "texto", 85), Coluna("Descrição", "texto", 160), Coluna("Valor", "num", 90), Coluna("Situação", "emblema", 90, tons)],
            vazio_titulo="Sem vencimentos",
            vazio_texto="Nenhum lançamento em aberto para os próximos dias.",
            placeholder="Buscar lançamento…",
        )
        tabela.definir_dados([(i, [data, tipo, desc, Decimal(valor), "Vencido" if vencido else "No prazo"]) for i, (data, tipo, desc, valor, vencido) in enumerate(linhas)])
        tabela.setMinimumHeight(250)
        tabela.ativado.connect(lambda _iid: self.ir_para("Financeiro"))
        corpo.addWidget(tabela)
        return card

    def focar_busca(self) -> bool:
        return False


__all__ = ["PaginaDashboard"]
