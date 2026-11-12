"""Graficos interativos desenhados com QPainter (QtCharts nao faz parte do PySide6-Essentials)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from app.ui.tema import ao_mudar_tema, tema
from app.utils.formatacao import format_value


def moeda_curta(valor: float) -> str:
    """1.250 -> '1,3 mil'; 2.500.000 -> '2,5 mi'; abaixo de mil mostra inteiro."""
    absoluto = abs(valor)

    def um_decimal(numero: float) -> str:  # arredonda metade para cima (1,25 -> 1,3)
        return str(Decimal(str(numero)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)).replace(".", ",")

    if absoluto >= 1_000_000:
        return f"{um_decimal(valor / 1_000_000)} mi"
    if absoluto >= 1_000:
        return f"{um_decimal(valor / 1_000)} mil"
    return f"{valor:.0f}"


def reais(valor) -> str:
    return "R$ " + format_value(Decimal(valor))


class GraficoBarras(QWidget):
    """Barras verticais com crescimento animado, destaque ao passar o mouse e clique por barra.

    `definir_dados([(rotulo, valor), ...])`; a ultima barra e a destacada (periodo atual).
    """

    clicada = Signal(int)

    def __init__(self, formatar=reais, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dados: list[tuple[str, float]] = []
        self._formatar = formatar
        self._progresso = 1.0
        self._sobre = -1
        self._retangulos: list[QRectF] = []
        self.setMouseTracking(True)
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._animacao = QVariantAnimation(self)
        self._animacao.setStartValue(0.0)
        self._animacao.setEndValue(1.0)
        self._animacao.setDuration(650)
        self._animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animacao.valueChanged.connect(self._passo)
        ao_mudar_tema(self, self.update)

    def definir_dados(self, dados, animar: bool = True) -> None:
        self._dados = [(str(r), float(v)) for r, v in dados]
        self._sobre = -1
        if animar:
            self._animacao.stop()
            self._progresso = 0.0
            self._animacao.start()
        else:
            self._progresso = 1.0
        self.update()

    def dados(self) -> list[tuple[str, float]]:
        return list(self._dados)

    def _passo(self, valor) -> None:
        self._progresso = float(valor)
        self.update()

    # ---- interacao
    def _indice_em(self, ponto: QPointF) -> int:
        for i, area in enumerate(self._retangulos):
            if QRectF(area.left(), 0, area.width(), self.height()).contains(ponto):
                return i
        return -1

    def mouseMoveEvent(self, evento) -> None:  # noqa: N802
        indice = self._indice_em(evento.position())
        if indice != self._sobre:
            self._sobre = indice
            self.update()
        if indice >= 0:
            rotulo, valor = self._dados[indice]
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            QToolTip.showText(evento.globalPosition().toPoint(), f"{rotulo}: {self._formatar(valor)}", self)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            QToolTip.hideText()

    def leaveEvent(self, evento) -> None:  # noqa: N802
        self._sobre = -1
        self.update()
        super().leaveEvent(evento)

    def mouseReleaseEvent(self, evento) -> None:  # noqa: N802
        if evento.button() == Qt.MouseButton.LeftButton:
            indice = self._indice_em(evento.position())
            if indice >= 0:
                self.clicada.emit(indice)

    # ---- desenho
    def paintEvent(self, _evento) -> None:  # noqa: N802
        t = tema.t
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        largura, altura = self.width(), self.height()
        base, topo, esq = 30, 26, 8
        area_h = altura - base - topo
        self._retangulos = []
        maior = max((v for _, v in self._dados), default=0.0)
        fonte = QFont(self.font())
        fonte.setPointSizeF(9)
        p.setFont(fonte)
        if not self._dados or maior <= 0:
            p.setPen(QColor(t["mudo"]))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sem vendas finalizadas no período")
            return
        # linhas-guia
        p.setPen(QPen(QColor(t["borda"]), 1, Qt.PenStyle.DashLine))
        for fracao in (0.25, 0.5, 0.75, 1.0):
            y = altura - base - area_h * fracao
            p.drawLine(QPointF(esq, y), QPointF(largura - esq, y))
        p.setPen(QPen(QColor(t["borda_forte"]), 1))
        p.drawLine(QPointF(esq, altura - base), QPointF(largura - esq, altura - base))
        faixa = (largura - esq * 2) / len(self._dados)
        largura_barra = min(faixa * 0.56, 72)
        for i, (rotulo, valor) in enumerate(self._dados):
            x0 = esq + faixa * i + (faixa - largura_barra) / 2
            h = valor / maior * area_h * self._progresso
            ultimo, sobre = i == len(self._dados) - 1, i == self._sobre
            self._retangulos.append(QRectF(esq + faixa * i, 0, faixa, altura))
            cor = QColor(t["primaria"])
            if not ultimo:
                cor.setAlphaF(0.95 if sobre else 0.45)
            elif sobre:
                cor = QColor(t["primaria_hover"])
            if h > 0:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(cor)
                p.drawRoundedRect(QRectF(x0, altura - base - h, largura_barra, h), 6, 6)
            p.setPen(QColor(t["texto"] if (ultimo or sobre) else t["texto2"]))
            negrito = QFont(fonte)
            negrito.setBold(ultimo or sobre)
            p.setFont(negrito)
            if h > 14:
                p.drawText(QRectF(x0 - 20, altura - base - h - 20, largura_barra + 40, 18), Qt.AlignmentFlag.AlignCenter, moeda_curta(valor * self._progresso))
            p.setFont(fonte)
            p.setPen(QColor(t["texto"] if (ultimo or sobre) else t["mudo"]))
            p.drawText(QRectF(x0 - 20, altura - base + 6, largura_barra + 40, 18), Qt.AlignmentFlag.AlignCenter, rotulo)


class BarraComparativa(QWidget):
    """Duas barras horizontais lado a lado na mesma escala (ex.: a receber x a pagar em 7 dias)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._itens: list[tuple[str, float, str]] = []
        self.setMinimumHeight(96)
        ao_mudar_tema(self, self.update)

    def definir(self, itens: list[tuple[str, float, str]]) -> None:
        """itens: (rotulo, valor, tom) com tom em 'sucesso'|'perigo'|'aviso'|'info'|'primaria'."""
        self._itens = [(r, float(v), tom) for r, v, tom in itens]
        self.update()

    def paintEvent(self, _evento) -> None:  # noqa: N802
        t = tema.t
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._itens:
            return
        maior = max((v for _, v, _ in self._itens), default=0.0) or 1.0
        linha_h = self.height() / len(self._itens)
        fonte = QFont(self.font())
        fonte.setPointSizeF(9)
        p.setFont(fonte)
        for i, (rotulo, valor, tom) in enumerate(self._itens):
            y = linha_h * i
            p.setPen(QColor(t["texto2"]))
            p.drawText(QRectF(0, y, self.width() * 0.6, 20), Qt.AlignmentFlag.AlignVCenter, rotulo)
            p.setPen(QColor(t["texto"]))
            p.drawText(QRectF(0, y, self.width(), 20), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, reais(valor))
            trilho = QRectF(0, y + 24, self.width(), 8)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t["borda"]))
            p.drawRoundedRect(trilho, 4, 4)
            if valor > 0:
                p.setBrush(QColor(t[tom]))
                p.drawRoundedRect(QRectF(0, y + 24, max(8.0, self.width() * valor / maior), 8), 4, 4)
