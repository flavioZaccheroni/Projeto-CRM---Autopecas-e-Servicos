"""Casca do aplicativo: barra lateral recolhivel, cabecalho, paleta de comandos e janela principal."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPropertyAnimation, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import APP_VERSION, AVISO_DEMO, AVISO_DEMO_CURTO
from app.ui import icones
from app.ui.componentes import Avisos, Botao, EstadoVazio, rotulo
from app.ui.tema import ao_mudar_tema, tema
from app.utils.busca import normalizar
from app.utils.sessao import MENU_PARA_MODULO, Sessao

LARGURA_ABERTA = 252
LARGURA_FECHADA = 72


@dataclass(frozen=True)
class ItemMenu:
    chave: str  # igual ao nome em MENU_PARA_MODULO
    rotulo: str
    icone: str


GRUPOS: list[tuple[str, list[ItemMenu]]] = [
    ("Principal", [ItemMenu("Dashboard", "Dashboard", "dashboard")]),
    (
        "Cadastros",
        [
            ItemMenu("Clientes", "Clientes", "usuarios"),
            ItemMenu("Veiculos", "Veículos", "carro"),
            ItemMenu("Fornecedores", "Fornecedores", "caminhao"),
            ItemMenu("Categorias", "Categorias", "camadas"),
            ItemMenu("Marcas", "Marcas", "etiqueta"),
            ItemMenu("Produtos", "Produtos", "pacote"),
        ],
    ),
    (
        "Operação",
        [
            ItemMenu("Estoque", "Estoque", "estoque"),
            ItemMenu("Compras", "Compras", "carrinho"),
            ItemMenu("Vendas", "Vendas", "recibo"),
            ItemMenu("Ordem de Servico", "Ordem de serviço", "chave"),
            ItemMenu("Financeiro", "Financeiro", "carteira"),
            ItemMenu("Relatorios", "Relatórios", "grafico"),
        ],
    ),
    (
        "Sistema",
        [
            ItemMenu("Seguranca e Backup", "Segurança e backup", "escudo"),
            ItemMenu("Usuarios", "Usuários", "usuario"),
            ItemMenu("Permissoes", "Permissões", "cadeado"),
            ItemMenu("Configuracoes", "Configurações", "ajustes"),
        ],
    ),
]


if os.environ.get("ERP_UI_GALERIA"):  # vitrine do design system, so para desenvolvimento
    GRUPOS[-1][1].append(ItemMenu("Galeria", "Galeria de componentes", "camadas"))


def pode_ver(chave: str) -> bool:
    modulo = MENU_PARA_MODULO.get(chave)
    return modulo is None or Sessao.pode(modulo, "ver")


# ------------------------------------------------------------------------------- barra lateral
class BotaoNav(QPushButton):
    def __init__(self, item: ItemMenu) -> None:
        super().__init__()
        self.item = item
        self.setProperty("papel", "nav")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(18, 18))
        self.setMinimumHeight(40)
        self.recolher(False)
        self.toggled.connect(lambda _: self._icone())
        ao_mudar_tema(self, self._icone)
        self._icone()

    def _icone(self) -> None:
        t = tema.t
        self.setIcon(icones.icone(self.item.icone, "#ffffff" if self.isChecked() else t["lateral_texto"], 18))

    def recolher(self, recolhido: bool) -> None:
        self.setText("" if recolhido else "  " + self.item.rotulo)
        self.setToolTip(self.item.rotulo if recolhido else "")


class BarraLateral(QFrame):
    navegar = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Lateral")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(LARGURA_ABERTA)
        self.recolhida = False
        self._botoes: dict[str, BotaoNav] = {}
        self._grupos: list[QLabel] = []
        self._animacao: QVariantAnimation | None = None

        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(12, 14, 12, 12)
        corpo.setSpacing(2)
        marca = QHBoxLayout()
        marca.setSpacing(10)
        self.logo = QLabel()
        self.logo.setFixedSize(34, 34)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nome = rotulo("ERP Autopeças", "marca")
        marca.addWidget(self.logo)
        marca.addWidget(self.nome)
        marca.addStretch()
        corpo.addLayout(marca)
        corpo.addSpacing(14)

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        for nome_grupo, itens in GRUPOS:
            visiveis = [i for i in itens if pode_ver(i.chave)]
            if not visiveis:
                continue
            titulo = rotulo(nome_grupo.upper(), "grupo")
            titulo.setContentsMargins(8, 10, 0, 4)
            self._grupos.append(titulo)
            corpo.addWidget(titulo)
            for item in visiveis:
                botao = BotaoNav(item)
                botao.clicked.connect(lambda _=False, chave=item.chave: self.navegar.emit(chave))
                self._grupo.addButton(botao)
                self._botoes[item.chave] = botao
                corpo.addWidget(botao)
        corpo.addStretch()
        self.versao = rotulo(f"Versão {APP_VERSION}\n{AVISO_DEMO_CURTO}", "grupo")
        self.versao.setToolTip(AVISO_DEMO)
        self.versao.setContentsMargins(8, 0, 0, 4)
        corpo.addWidget(self.versao)
        ao_mudar_tema(self, self._logo)
        self._logo()

    def _logo(self) -> None:
        self.logo.setStyleSheet(f"background: {tema.t['lateral_ativo']}; border-radius: 9px;")
        self.logo.setPixmap(icones.pixmap("chave", "#ffffff", 18))

    def marcar(self, chave: str) -> None:
        botao = self._botoes.get(chave)
        if botao:
            botao.setChecked(True)

    def tem(self, chave: str) -> bool:
        return chave in self._botoes

    def alternar(self) -> None:
        self.recolhida = not self.recolhida
        origem, destino = self.width(), LARGURA_FECHADA if self.recolhida else LARGURA_ABERTA
        if not self.recolhida:
            self._aplicar_modo()
        animacao = QVariantAnimation(self)
        animacao.setStartValue(origem)
        animacao.setEndValue(destino)
        animacao.setDuration(220)
        animacao.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animacao.valueChanged.connect(lambda v: self.setFixedWidth(int(v)))
        if self.recolhida:
            animacao.finished.connect(self._aplicar_modo)
        self._animacao = animacao
        animacao.start()

    def _aplicar_modo(self) -> None:
        for botao in self._botoes.values():
            botao.recolher(self.recolhida)
        for titulo in self._grupos:
            titulo.setVisible(not self.recolhida)
        self.nome.setVisible(not self.recolhida)
        self.versao.setVisible(not self.recolhida)


# ------------------------------------------------------------------------------- cabecalho
class Cabecalho(QFrame):
    menu_clicado = Signal()
    paleta_clicada = Signal()
    tema_clicado = Signal()
    atualizar_clicado = Signal()
    sair_clicado = Signal()

    def __init__(self, usuario) -> None:
        super().__init__()
        self.setObjectName("Cabecalho")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(64)
        linha = QHBoxLayout(self)
        linha.setContentsMargins(16, 0, 20, 0)
        linha.setSpacing(8)
        self.botao_menu = Botao("", "icone", "menu")
        self.botao_menu.setToolTip("Recolher menu (Ctrl+B)")
        self.botao_menu.clicked.connect(self.menu_clicado)
        titulos = QVBoxLayout()
        titulos.setSpacing(0)
        self.titulo = rotulo("", "secao")
        self.subtitulo = rotulo("", "mudo")
        titulos.addStretch()
        titulos.addWidget(self.titulo)
        titulos.addWidget(self.subtitulo)
        titulos.addStretch()
        self.busca = QPushButton("  Buscar ou ir para…      Ctrl+K")
        self.busca.setObjectName("Busca")
        self.busca.setCursor(Qt.CursorShape.PointingHandCursor)
        self.busca.setMinimumWidth(300)
        self.busca.clicked.connect(self.paleta_clicada)
        self.busca.setIcon(icones.icone("buscar", tema.t["mudo"], 16))
        self.botao_atualizar = Botao("", "icone", "atualizar")
        self.botao_atualizar.setToolTip("Atualizar (F5)")
        self.botao_atualizar.clicked.connect(self.atualizar_clicado)
        self.botao_tema = Botao("", "icone", "lua")
        self.botao_tema.clicked.connect(self.tema_clicado)
        self.avatar = QLabel((usuario.nome or "?")[:1].upper())
        self.avatar.setObjectName("Avatar")
        self.avatar.setFixedSize(32, 32)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quem = QVBoxLayout()
        quem.setSpacing(0)
        quem.addStretch()
        quem.addWidget(rotulo(usuario.nome, "rotulo"))
        quem.addWidget(rotulo(usuario.perfil.nome, "mudo"))
        quem.addStretch()
        self.botao_usuario = QPushButton()
        self.botao_usuario.setProperty("variante", "fantasma")
        self.botao_usuario.setCursor(Qt.CursorShape.PointingHandCursor)
        interno = QHBoxLayout(self.botao_usuario)
        interno.setContentsMargins(6, 2, 8, 2)
        interno.setSpacing(8)
        interno.addWidget(self.avatar)
        interno.addLayout(quem)
        self.botao_usuario.setFixedHeight(46)
        self.botao_usuario.setMinimumWidth(170)
        self.botao_usuario.setStyleSheet("QPushButton::menu-indicator { image: none; width: 0px; }")
        menu = QMenu(self.botao_usuario)
        acao_sair = QAction("Sair", menu)
        acao_sair.triggered.connect(self.sair_clicado)
        menu.addAction(acao_sair)
        self.botao_usuario.setMenu(menu)
        linha.addWidget(self.botao_menu)
        linha.addLayout(titulos)
        linha.addStretch()
        linha.addWidget(self.busca)
        linha.addWidget(self.botao_atualizar)
        linha.addWidget(self.botao_tema)
        linha.addSpacing(6)
        linha.addWidget(self.botao_usuario)
        tema.mudou.connect(self._pintar)
        self._pintar()

    def _pintar(self, *_args) -> None:
        self.botao_tema.definir_icone("sol" if tema.modo == "escuro" else "lua")
        self.botao_tema.setToolTip("Tema claro" if tema.modo == "escuro" else "Tema escuro")
        self.busca.setIcon(icones.icone("buscar", tema.t["mudo"], 16))

    def definir_pagina(self, titulo: str, subtitulo: str = "") -> None:
        self.titulo.setText(titulo)
        self.subtitulo.setText(subtitulo)


# ------------------------------------------------------------------------------- paleta de comandos
@dataclass
class Acao:
    rotulo: str
    grupo: str
    icone: str
    executar: Callable[[], None]


class PaletaComandos(QDialog):
    """Ctrl+K: busca por telas e acoes, navegavel so pelo teclado."""

    def __init__(self, parent: QWidget, acoes: list[Acao]) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._acoes = acoes
        externo = QVBoxLayout(self)
        externo.setContentsMargins(24, 24, 24, 24)
        quadro = QFrame()
        quadro.setObjectName("Paleta")
        quadro.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sombra = QGraphicsDropShadowEffect(quadro)
        sombra.setBlurRadius(40)
        sombra.setOffset(0, 10)
        sombra.setColor(Qt.GlobalColor.black)
        quadro.setGraphicsEffect(sombra)
        externo.addWidget(quadro)
        corpo = QVBoxLayout(quadro)
        corpo.setContentsMargins(0, 0, 0, 0)
        corpo.setSpacing(0)
        self.campo = QLineEdit()
        self.campo.setPlaceholderText("Digite o nome de uma tela ou ação…")
        self.lista = QListWidget()
        self.lista.setIconSize(QSize(18, 18))
        corpo.addWidget(self.campo)
        corpo.addWidget(self.lista)
        self.resize(560, 420)
        self.campo.textChanged.connect(self._filtrar)
        self.campo.installEventFilter(self)
        self.lista.itemActivated.connect(self._executar)
        self.lista.itemClicked.connect(self._executar)
        self._filtrar("")

    def showEvent(self, evento) -> None:  # noqa: N802
        pai = self.parentWidget()
        if pai:
            centro = pai.mapToGlobal(pai.rect().center())
            self.move(centro.x() - self.width() // 2, pai.mapToGlobal(pai.rect().topLeft()).y() + 90)
        self.campo.setFocus()
        super().showEvent(evento)

    def _filtrar(self, termo: str) -> None:
        palavras = normalizar(termo).split()
        self.lista.clear()
        for acao in self._acoes:
            alvo = normalizar(f"{acao.rotulo} {acao.grupo}")
            if all(p in alvo for p in palavras):
                item = QListWidgetItem(icones.icone(acao.icone, tema.t["texto2"], 18), f"{acao.rotulo}    ·    {acao.grupo}")
                item.setData(Qt.ItemDataRole.UserRole, acao)
                self.lista.addItem(item)
        if self.lista.count():
            self.lista.setCurrentRow(0)

    def _executar(self, item: QListWidgetItem) -> None:
        acao: Acao = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        acao.executar()

    def eventFilter(self, origem: QObject, evento: QEvent) -> bool:  # noqa: N802
        if origem is self.campo and evento.type() == QEvent.Type.KeyPress:
            tecla = evento.key()
            if tecla in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                passo = 1 if tecla == Qt.Key.Key_Down else -1
                self.lista.setCurrentRow(max(0, min(self.lista.count() - 1, self.lista.currentRow() + passo)))
                return True
            if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.lista.currentItem():
                    self._executar(self.lista.currentItem())
                return True
        return super().eventFilter(origem, evento)


# ------------------------------------------------------------------------------- janela principal
class JanelaPrincipal(QMainWindow):
    sair_solicitado = Signal()

    def __init__(self, usuario, fabricas: dict[str, Callable[[], QWidget]] | None = None) -> None:
        super().__init__()
        self.usuario = usuario
        self.fabricas = fabricas or {}
        self.setWindowTitle("ERP CRM Autopeças & Serviços — Versão de demonstração")
        self.resize(1360, 820)
        self.setMinimumSize(1060, 660)
        self._paginas: dict[str, QWidget] = {}
        self._atual: str | None = None

        raiz = QWidget()
        raiz.setObjectName("Raiz")
        self.setCentralWidget(raiz)
        linha = QHBoxLayout(raiz)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(0)
        self.lateral = BarraLateral()
        coluna = QVBoxLayout()
        coluna.setSpacing(0)
        self.cabecalho = Cabecalho(usuario)
        self.pilha = QStackedWidget()
        coluna.addWidget(self.cabecalho)
        coluna.addWidget(self.pilha, 1)
        linha.addWidget(self.lateral)
        linha.addLayout(coluna, 1)
        self.avisos = Avisos(self)

        self.lateral.navegar.connect(self.abrir)
        self.cabecalho.menu_clicado.connect(self.lateral.alternar)
        self.cabecalho.paleta_clicada.connect(self.abrir_paleta)
        self.cabecalho.tema_clicado.connect(tema.alternar)
        self.cabecalho.atualizar_clicado.connect(self.recarregar)
        self.cabecalho.sair_clicado.connect(self.sair_solicitado)
        for atalho, funcao in (
            ("F5", self.recarregar),
            ("Ctrl+F", self.focar_busca),
            ("Ctrl+K", self.abrir_paleta),
            ("Ctrl+B", self.lateral.alternar),
        ):
            QShortcut(QKeySequence(atalho), self, activated=funcao)

        self.abrir("Dashboard" if self.lateral.tem("Dashboard") else next(iter(self.lateral._botoes), "Dashboard"))

    # navegacao
    def abrir(self, chave: str) -> None:
        if not pode_ver(chave):
            self.avisos.mostrar("Você não tem acesso a esta tela.", "perigo")
            return
        pagina = self._paginas.get(chave)
        if pagina is None:
            pagina = self._criar_pagina(chave)
            self._paginas[chave] = pagina
            self.pilha.addWidget(pagina)
        self._atual = chave
        self.lateral.marcar(chave)
        titulo = next((i.rotulo for _, itens in GRUPOS for i in itens if i.chave == chave), chave)
        self.cabecalho.definir_pagina(titulo, getattr(pagina, "subtitulo", ""))
        self.pilha.setCurrentWidget(pagina)
        self._transicao(pagina)
        if hasattr(pagina, "ao_abrir"):
            pagina.ao_abrir()

    def _criar_pagina(self, chave: str) -> QWidget:
        fabrica = self.fabricas.get(chave)
        if fabrica:
            return fabrica()
        quadro = QWidget()
        corpo = QVBoxLayout(quadro)
        vazio = EstadoVazio("Tela em redesenho", "Esta área será entregue nas próximas fases do novo design.", "ajustes")
        corpo.addWidget(vazio)
        return quadro

    def _transicao(self, pagina: QWidget) -> None:
        efeito = QGraphicsOpacityEffect(pagina)
        pagina.setGraphicsEffect(efeito)
        animacao = QPropertyAnimation(efeito, b"opacity", pagina)
        animacao.setDuration(200)
        animacao.setStartValue(0.0)
        animacao.setEndValue(1.0)
        animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        animacao.finished.connect(lambda: pagina.setGraphicsEffect(None))
        animacao.start()
        pagina._animacao_entrada = animacao

    def recarregar(self) -> None:
        pagina = self._paginas.get(self._atual or "")
        if pagina is not None and hasattr(pagina, "recarregar"):
            pagina.recarregar()
            self.avisos.mostrar("Dados atualizados.", "sucesso", 1800)

    def focar_busca(self) -> None:
        pagina = self._paginas.get(self._atual or "")
        if pagina is not None and hasattr(pagina, "focar_busca") and pagina.focar_busca():
            return

    def abrir_paleta(self) -> None:
        acoes = [
            Acao(item.rotulo, "Ir para", item.icone, lambda c=item.chave: self.abrir(c))
            for _, itens in GRUPOS
            for item in itens
            if self.lateral.tem(item.chave)
        ]
        acoes += [
            Acao("Alternar tema claro/escuro", "Ação", "lua", tema.alternar),
            Acao("Recolher/expandir menu", "Ação", "menu", self.lateral.alternar),
            Acao("Atualizar tela atual", "Ação", "atualizar", self.recarregar),
            Acao("Sair", "Ação", "sair", self.sair_solicitado.emit),
        ]
        PaletaComandos(self, acoes).exec()

    def showEvent(self, evento) -> None:  # noqa: N802
        super().showEvent(evento)
        tela = QGuiApplication.primaryScreen()
        if tela and not getattr(self, "_centralizada", False):
            self._centralizada = True
            self.move(tela.availableGeometry().center() - self.rect().center())

