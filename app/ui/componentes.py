"""Componentes reutilizaveis do redesign: botao, cartao, KPI, emblema, busca, tabela de dados, seletor, avisos."""

from __future__ import annotations

import csv
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from PySide6.QtCore import (
    QAbstractTableModel,
    QEasingCurve,
    QEvent,
    QModelIndex,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRectF,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCompleter,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedLayout,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.ui import icones
from app.ui.tema import ao_mudar_tema, cor_do_tom, tema
from app.utils.busca import extrair_id, normalizar
from app.utils.formatacao import format_value


def rotulo(texto: str = "", papel: str = "", parent: QWidget | None = None, quebra: bool = False) -> QLabel:
    """QLabel com um papel tipografico definido no tema (titulo, subtitulo, secao, mudo, erro, kpi, rotulo)."""
    label = QLabel(texto, parent)
    if papel:
        label.setProperty("papel", papel)
    label.setWordWrap(quebra)
    return label


def _repolir(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


# ---------------------------------------------------------------------------------------- botao
class Botao(QPushButton):
    """Botao com variantes: secundario (padrao), primario, perigo, fantasma e icone."""

    def __init__(self, texto: str = "", variante: str = "secundario", icone: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(texto, parent)
        self._icone = icone
        self.setProperty("variante", variante)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if variante == "icone":
            self.setFixedSize(36, 36)
        tema.mudou.connect(self._atualizar_icone)
        self._atualizar_icone()

    def definir_icone(self, nome: str | None) -> None:
        self._icone = nome
        self._atualizar_icone()

    def _atualizar_icone(self, *_args) -> None:
        if not self._icone:
            return
        t = tema.t
        variante = self.property("variante")
        cor = {"primario": t["sobre_primaria"], "perigo": t["perigo"]}.get(variante, t["texto2"])
        self.setIcon(icones.icone(self._icone, cor, 18))


# ---------------------------------------------------------------------------------------- cartao
class Card(QFrame):
    """Superficie com borda, raio e sombra suave."""

    def __init__(self, parent: QWidget | None = None, sombra: bool = True) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._sombra = None
        if sombra:
            self._sombra = QGraphicsDropShadowEffect(self)
            self._sombra.setBlurRadius(22)
            self._sombra.setOffset(0, 3)
            self.setGraphicsEffect(self._sombra)
            tema.mudou.connect(self._cor_sombra)
            self._cor_sombra()

    def _cor_sombra(self, *_args) -> None:
        if self._sombra is not None:
            cor = QColor(tema.t["sombra"])
            cor.setAlpha(28 if tema.modo == "claro" else 90)
            self._sombra.setColor(cor)


class Emblema(QLabel):
    """Pilula colorida para status (tons: neutro, primaria, sucesso, aviso, perigo, info)."""

    def __init__(self, texto: str = "", tom: str = "neutro", parent: QWidget | None = None) -> None:
        super().__init__(texto, parent)
        self.setProperty("papel", "emblema")
        self._tom = tom
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tema.mudou.connect(self._pintar)
        self._pintar()

    def definir(self, texto: str, tom: str) -> None:
        self.setText(texto)
        self._tom = tom
        self._pintar()

    def _pintar(self, *_args) -> None:
        forte, suave = cor_do_tom(tema.t, self._tom)
        self.setStyleSheet(f"QLabel {{ color: {forte}; background: {suave}; border-radius: 9px; padding: 2px 9px; font-weight: 700; font-size: 11px; }}")


class KpiCard(Card):
    """Indicador: titulo, valor grande (com contagem animada), nota e icone em destaque. Pode ser clicavel."""

    clicado = Signal()

    def __init__(self, titulo: str, icone: str = "grafico", tom: str = "primaria", nota: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icone, self._tom = icone, tom
        self._animacao: QVariantAnimation | None = None
        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(18, 16, 18, 16)
        corpo.setSpacing(4)
        topo = QHBoxLayout()
        self.titulo = rotulo(titulo.upper(), "rotulo")
        self.chip = QLabel()
        self.chip.setObjectName("IconeKpi")
        self.chip.setFixedSize(36, 36)
        self.chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        topo.addWidget(self.titulo)
        topo.addStretch()
        topo.addWidget(self.chip)
        self.valor = rotulo("-", "kpi")
        self.nota = rotulo(nota, "mudo", quebra=True)
        corpo.addLayout(topo)
        corpo.addWidget(self.valor)
        corpo.addWidget(self.nota)
        tema.mudou.connect(self._pintar)
        self._pintar()

    def _pintar(self, *_args) -> None:
        forte, suave = cor_do_tom(tema.t, self._tom)
        self.chip.setStyleSheet(f"background: {suave}; border-radius: 12px;")
        self.chip.setPixmap(icones.pixmap(self._icone, forte, 18))

    def definir_tom(self, tom: str) -> None:
        self._tom = tom
        self._pintar()

    def definir_valor(self, texto: str, nota: str | None = None) -> None:
        self.valor.setText(texto)
        if nota is not None:
            self.nota.setText(nota)

    def animar_para(self, alvo: float, formato: Callable[[float], str], nota: str | None = None, ms: int = 650) -> None:
        """Conta de 0 ate `alvo` formatando cada passo (ex.: moeda)."""
        if self._animacao is not None:
            self._animacao.stop()
        if nota is not None:
            self.nota.setText(nota)
        animacao = QVariantAnimation(self)
        animacao.setStartValue(0.0)
        animacao.setEndValue(float(alvo))
        animacao.setDuration(ms)
        animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        animacao.valueChanged.connect(lambda v: self.valor.setText(formato(float(v))))
        animacao.finished.connect(lambda: self.valor.setText(formato(float(alvo))))
        self._animacao = animacao
        animacao.start()

    def tornar_clicavel(self, ativo: bool = True) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor if ativo else Qt.CursorShape.ArrowCursor)
        self.setProperty("destaque", False)
        self._clicavel = ativo

    def enterEvent(self, event) -> None:  # noqa: N802
        if getattr(self, "_clicavel", False):
            self.setProperty("destaque", True)
            _repolir(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        if getattr(self, "_clicavel", False):
            self.setProperty("destaque", False)
            _repolir(self)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if getattr(self, "_clicavel", False) and event.button() == Qt.MouseButton.LeftButton:
            self.clicado.emit()
        super().mouseReleaseEvent(event)


class EstadoVazio(QWidget):
    """Mensagem amigavel para listas sem dados, com acao opcional."""

    def __init__(self, titulo: str, texto: str = "", icone: str = "pacote", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        corpo = QVBoxLayout(self)
        corpo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        corpo.setSpacing(8)
        self._icone = icone
        self.figura = QLabel()
        self.figura.setFixedSize(64, 64)
        self.figura.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titulo = rotulo(titulo, "secao")
        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto = rotulo(texto, "mudo", quebra=True)
        self.texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.texto.setMaximumWidth(360)
        corpo.addWidget(self.figura, 0, Qt.AlignmentFlag.AlignCenter)
        corpo.addWidget(self.titulo)
        corpo.addWidget(self.texto, 0, Qt.AlignmentFlag.AlignCenter)
        self.acao: Botao | None = None
        tema.mudou.connect(self._pintar)
        self._pintar()

    def definir_acao(self, texto: str, callback: Callable[[], None], icone: str = "mais") -> None:
        if self.acao is None:
            self.acao = Botao(texto, "primario", icone)
            self.layout().addSpacing(6)
            self.layout().addWidget(self.acao, 0, Qt.AlignmentFlag.AlignCenter)
        self.acao.setText(texto)
        self.acao.clicked.connect(callback)

    def _pintar(self, *_args) -> None:
        self.figura.setStyleSheet(f"background: {tema.t['superficie2']}; border-radius: 32px;")
        self.figura.setPixmap(icones.pixmap(self._icone, tema.t["mudo"], 28))


class CaixaBusca(QLineEdit):
    """Campo de busca com lupa e botao de limpar."""

    def __init__(self, placeholder: str = "Buscar...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self._lupa = self.addAction(icones.icone("buscar", tema.t["mudo"], 16), QLineEdit.ActionPosition.LeadingPosition)
        ao_mudar_tema(self, lambda: self._lupa.setIcon(icones.icone("buscar", tema.t["mudo"], 16)))
        self.setMinimumWidth(260)


# ---------------------------------------------------------------------------------------- tabela
@dataclass
class Coluna:
    titulo: str
    tipo: str = "texto"  # texto | num | data | emblema
    largura: int | None = None
    tons: dict[str, str] | None = None  # emblema: valor -> tom


PAPEL_ORDEM = Qt.ItemDataRole.UserRole
PAPEL_ID = Qt.ItemDataRole.UserRole + 1
PAPEL_TOM = Qt.ItemDataRole.UserRole + 2


class ModeloTabela(QAbstractTableModel):
    def __init__(self, colunas: list[Coluna]) -> None:
        super().__init__()
        self.colunas = colunas
        self._linhas: list[tuple[object, list]] = []
        self._busca: list[str] = []

    def definir(self, linhas: Iterable[tuple[object, list]]) -> None:
        self.beginResetModel()
        self._linhas = [(iid, list(valores)) for iid, valores in linhas]
        self._busca = [normalizar(" ".join(format_value(v) for v in valores)) for _, valores in self._linhas]
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802, B008
        return 0 if parent.isValid() else len(self._linhas)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802, B008
        return 0 if parent.isValid() else len(self.colunas)

    def texto_busca(self, linha: int) -> str:
        return self._busca[linha]

    def headerData(self, secao: int, orientacao: Qt.Orientation, papel: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if orientacao == Qt.Orientation.Horizontal and papel == Qt.ItemDataRole.DisplayRole:
            return self.colunas[secao].titulo
        return None

    def data(self, indice: QModelIndex, papel: int = Qt.ItemDataRole.DisplayRole):
        if not indice.isValid():
            return None
        iid, valores = self._linhas[indice.row()]
        coluna = self.colunas[indice.column()]
        bruto = valores[indice.column()] if indice.column() < len(valores) else None
        if papel == Qt.ItemDataRole.DisplayRole:
            return format_value(bruto)
        if papel == PAPEL_ORDEM:
            return bruto
        if papel == PAPEL_ID:
            return iid
        if papel == PAPEL_TOM:
            return (coluna.tons or {}).get(str(bruto), "neutro") if coluna.tipo == "emblema" else None
        if papel == Qt.ItemDataRole.TextAlignmentRole:
            alinhamento = Qt.AlignmentFlag.AlignRight if coluna.tipo == "num" else Qt.AlignmentFlag.AlignLeft
            return int(alinhamento | Qt.AlignmentFlag.AlignVCenter)
        return None


class ProxyTabela(QSortFilterProxyModel):
    """Filtro por todas as palavras (sem acento/caixa) e ordenacao pelo valor bruto (numero/data)."""

    def __init__(self) -> None:
        super().__init__()
        self._palavras: list[str] = []

    def definir_termo(self, termo: str) -> None:
        self._palavras = normalizar(termo).split()
        self.invalidateFilter()

    def filterAcceptsRow(self, linha: int, pai: QModelIndex) -> bool:  # noqa: N802
        if not self._palavras:
            return True
        texto = self.sourceModel().texto_busca(linha)
        return all(p in texto for p in self._palavras)

    def lessThan(self, esquerda: QModelIndex, direita: QModelIndex) -> bool:  # noqa: N802
        a, b = esquerda.data(PAPEL_ORDEM), direita.data(PAPEL_ORDEM)
        if a is None or b is None:
            return a is None and b is not None
        try:
            if isinstance(a, (int, float, Decimal)) and isinstance(b, (int, float, Decimal)):
                return a < b
            if isinstance(a, (date, datetime)) and isinstance(b, (date, datetime)):
                return a < b
        except TypeError:
            pass
        return normalizar(a) < normalizar(b)


class EmblemaDelegate(QStyledItemDelegate):
    """Desenha a celula como uma pilula colorida (status)."""

    def paint(self, pintor: QPainter, opcao: QStyleOptionViewItem, indice: QModelIndex) -> None:
        texto = indice.data(Qt.ItemDataRole.DisplayRole) or ""
        if not texto:
            return
        forte, suave = cor_do_tom(tema.t, indice.data(PAPEL_TOM) or "neutro")
        pintor.save()
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        fonte = pintor.font()
        fonte.setPointSizeF(8.5)
        fonte.setBold(True)
        pintor.setFont(fonte)
        largura = pintor.fontMetrics().horizontalAdvance(texto) + 20
        retangulo = QRectF(opcao.rect.left() + 8, opcao.rect.center().y() - 11, min(largura, opcao.rect.width() - 16), 22)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(suave))
        pintor.drawRoundedRect(retangulo, 11, 11)
        pintor.setPen(QColor(forte))
        pintor.drawText(retangulo, Qt.AlignmentFlag.AlignCenter, texto)
        pintor.restore()


class TabelaDados(QWidget):
    """Busca + contador + tabela ordenavel/filtravel + estado vazio. Sinais: selecionado(iid), ativado(iid)."""

    selecionado = Signal(object)
    ativado = Signal(object)

    def __init__(
        self,
        colunas: list[Coluna],
        vazio_titulo: str = "Nada por aqui ainda",
        vazio_texto: str = "Quando houver registros, eles aparecem nesta lista.",
        placeholder: str = "Buscar na lista...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.colunas = colunas
        self.modelo = ModeloTabela(colunas)
        self.proxy = ProxyTabela()
        self.proxy.setSourceModel(self.modelo)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(10)

        self.barra = QHBoxLayout()
        self.barra.setSpacing(10)
        self.busca = CaixaBusca(placeholder)
        self.contador = rotulo("", "mudo")
        self.barra.addWidget(self.busca)
        self.barra.addWidget(self.contador)
        self.barra.addStretch()
        raiz.addLayout(self.barra)

        self.tabela = QTableView()
        self.tabela.setModel(self.proxy)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setShowGrid(False)
        self.tabela.setWordWrap(False)
        self.tabela.setSortingEnabled(True)
        self.tabela.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tabela.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.verticalHeader().setDefaultSectionSize(42)
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setStretchLastSection(True)
        cabecalho.setSectionsMovable(True)
        cabecalho.setHighlightSections(False)
        cabecalho.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for indice, coluna in enumerate(colunas):
            cabecalho.setSectionResizeMode(indice, QHeaderView.ResizeMode.Interactive)
            self.tabela.setColumnWidth(indice, coluna.largura or 130)
            if coluna.tipo == "emblema":
                self.tabela.setItemDelegateForColumn(indice, EmblemaDelegate(self.tabela))

        self.vazio = EstadoVazio(vazio_titulo, vazio_texto)
        self.sem_resultado = EstadoVazio("Nenhum resultado", "Tente outras palavras ou limpe a busca.", "buscar")
        self._pilha = QStackedLayout()
        self._pilha.addWidget(self.tabela)
        self._pilha.addWidget(self.vazio)
        self._pilha.addWidget(self.sem_resultado)
        raiz.addLayout(self._pilha, 1)

        self.busca.textChanged.connect(self._ao_buscar)
        self.tabela.selectionModel().selectionChanged.connect(self._ao_selecionar)
        self.tabela.doubleClicked.connect(lambda i: self.ativado.emit(i.data(PAPEL_ID)))
        self.proxy.layoutChanged.connect(self._atualizar_estado)
        self.proxy.rowsInserted.connect(self._atualizar_estado)
        self.proxy.modelReset.connect(self._atualizar_estado)
        self._atualizar_estado()

    # dados
    def definir_dados(self, linhas: Iterable[tuple[object, list]]) -> None:
        iid = self.iid_atual()
        self.modelo.definir(linhas)
        self._atualizar_estado()
        if iid is not None:
            self.selecionar(iid)

    def adicionar_acao(self, widget: QWidget) -> None:
        self.barra.addWidget(widget)

    def total(self) -> int:
        return self.modelo.rowCount()

    # selecao
    def iid_atual(self):
        indices = self.tabela.selectionModel().selectedRows()
        return indices[0].data(PAPEL_ID) if indices else None

    def selecionar(self, iid) -> bool:
        for linha in range(self.proxy.rowCount()):
            indice = self.proxy.index(linha, 0)
            if indice.data(PAPEL_ID) == iid:
                self.tabela.selectRow(linha)
                return True
        return False

    def focar_busca(self) -> bool:
        self.busca.setFocus()
        self.busca.selectAll()
        return True

    def exportar_csv(self, caminho: str) -> int:
        """Exporta o que esta visivel (filtrado e ordenado). Retorna a quantidade de linhas."""
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow([c.titulo for c in self.colunas])
            for linha in range(self.proxy.rowCount()):
                escritor.writerow([self.proxy.index(linha, c).data() for c in range(len(self.colunas))])
        return self.proxy.rowCount()

    # internos
    def _ao_buscar(self, texto: str) -> None:
        self.proxy.definir_termo(texto)
        self._atualizar_estado()

    def _ao_selecionar(self) -> None:
        self.selecionado.emit(self.iid_atual())

    def _atualizar_estado(self, *_args) -> None:
        total, visiveis = self.modelo.rowCount(), self.proxy.rowCount()
        self.contador.setText(f"{visiveis} de {total}" if visiveis != total else f"{total} registro(s)")
        self._pilha.setCurrentIndex(0 if visiveis else (1 if not total else 2))


# ---------------------------------------------------------------------------------------- seletor
class Seletor(QComboBox):
    """Lista 'ID - nome' com busca ao digitar. `id()` devolve so o ID (ou '' se nada valido foi escolhido)."""

    escolhido = Signal(object)

    def __init__(self, carregar: Callable[[], Iterable[tuple]] | None = None, placeholder: str = "Digite para buscar...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._carregar = carregar
        self._opcoes: list[tuple] = []
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.lineEdit().setPlaceholderText(placeholder)
        completador = QCompleter(self.model(), self)
        completador.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completador.setFilterMode(Qt.MatchFlag.MatchContains)
        completador.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completador)
        self.setCurrentIndex(-1)
        self.activated.connect(self._ao_escolher)
        self.lineEdit().editingFinished.connect(self._validar)
        self.recarregar()

    @staticmethod
    def _texto(opcao: tuple) -> str:
        return f"{opcao[0]} - {opcao[1]}"

    def recarregar(self) -> None:
        atual = self.id()
        try:
            self._opcoes = list(self._carregar()) if self._carregar else []
        except Exception:  # noqa: BLE001 - sem permissao/sessao: o seletor fica vazio e a tela segue usavel
            self._opcoes = []
        self.blockSignals(True)
        self.clear()
        self.addItems([self._texto(o) for o in self._opcoes])
        self.blockSignals(False)
        self.definir_id(atual) if atual else self.setCurrentIndex(-1)

    def definir_opcoes(self, opcoes: Iterable[tuple]) -> None:
        self._carregar = lambda: opcoes
        self.recarregar()

    def id(self) -> str:
        return extrair_id(self.currentText())

    def opcao(self):
        atual = self.id()
        return next((o for o in self._opcoes if str(o[0]) == atual), None)

    def definir_id(self, valor) -> None:
        opcao = next((o for o in self._opcoes if str(o[0]) == str(valor)), None) if valor not in (None, "") else None
        self.setCurrentText(self._texto(opcao) if opcao else "")
        self._validar()

    def limpar(self) -> None:
        self.setCurrentIndex(-1)
        self.setCurrentText("")
        self._validar()

    def _ao_escolher(self, _indice: int) -> None:
        self._validar()
        self.escolhido.emit(self.opcao())

    def _validar(self) -> None:
        texto = self.currentText().strip()
        invalido = bool(texto) and self.opcao() is None
        if bool(self.property("invalido")) != invalido:
            self.setProperty("invalido", invalido)
            _repolir(self)


# ---------------------------------------------------------------------------------------- avisos
class _Aviso(QFrame):
    def __init__(self, texto: str, tom: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        icone = {"sucesso": "ok", "perigo": "alerta", "aviso": "alerta"}.get(tom, "info")
        forte, _ = cor_do_tom(tema.t, "primaria" if tom == "info" else tom)
        corpo = QHBoxLayout(self)
        corpo.setContentsMargins(14, 11, 16, 11)
        corpo.setSpacing(10)
        figura = QLabel()
        figura.setPixmap(icones.pixmap(icone, forte, 18))
        corpo.addWidget(figura)
        corpo.addWidget(QLabel(texto))
        self.adjustSize()


class Avisos(QObject):
    """Notificacoes temporarias no canto inferior direito da janela (sucesso/erro/info), empilhadas."""

    def __init__(self, janela: QWidget) -> None:
        super().__init__(janela)
        self._janela = janela
        self._ativos: list[_Aviso] = []
        janela.installEventFilter(self)

    def mostrar(self, texto: str, tom: str = "info", ms: int = 3400) -> None:
        aviso = _Aviso(texto, tom, self._janela)
        efeito = QGraphicsOpacityEffect(aviso)
        aviso.setGraphicsEffect(efeito)
        aviso.show()
        aviso.raise_()
        self._ativos.append(aviso)
        self._posicionar()
        entrada = QPropertyAnimation(efeito, b"opacity", aviso)
        entrada.setDuration(180)
        entrada.setStartValue(0.0)
        entrada.setEndValue(1.0)
        entrada.start()
        QTimer.singleShot(ms, lambda: self._sair(aviso, efeito))

    def _sair(self, aviso: _Aviso, efeito: QGraphicsOpacityEffect) -> None:
        saida = QPropertyAnimation(efeito, b"opacity", aviso)
        saida.setDuration(220)
        saida.setStartValue(1.0)
        saida.setEndValue(0.0)

        def _fim() -> None:
            if aviso in self._ativos:
                self._ativos.remove(aviso)
            aviso.deleteLater()
            self._posicionar()

        saida.finished.connect(_fim)
        saida.start()

    def _posicionar(self) -> None:
        y = self._janela.height() - 24
        for aviso in reversed(self._ativos):
            aviso.adjustSize()
            y -= aviso.height()
            aviso.move(QPoint(self._janela.width() - aviso.width() - 24, y))
            y -= 10

    def eventFilter(self, origem: QObject, evento: QEvent) -> bool:  # noqa: N802
        if origem is self._janela and evento.type() == QEvent.Type.Resize:
            self._posicionar()
        return False
