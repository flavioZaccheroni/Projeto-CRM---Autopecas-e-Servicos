"""Componentes das telas operacionais: etapas de status, tabela de itens editavel e dialogos (formulario, motivo, confirmacao)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.componentes import Botao, rotulo
from app.ui.formulario import Campo, Formulario
from app.ui.tema import ao_mudar_tema, tema
from app.utils.busca import valor_coluna
from app.utils.formatacao import format_value


# --------------------------------------------------------------------------------------- etapas
class EtapasStatus(QWidget):
    """Linha do tempo horizontal do status: etapas concluidas, a atual em destaque e as futuras apagadas.

    Estados terminais fora do fluxo (ex.: CANCELADA, RECUSADO) aparecem como um rotulo vermelho.
    """

    def __init__(self, etapas: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.etapas = etapas
        self._indice = -1
        self._terminal = ""
        self._rotulo_atual = ""
        self.setFixedHeight(58)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ao_mudar_tema(self, self.update)

    def definir(self, indice: int, terminal: str = "", rotulo_atual: str = "") -> None:
        """`indice`: etapa atual (-1 = nenhuma). `rotulo_atual` troca o texto da etapa atual (ex.: 'Aguardando peça')."""
        self._indice, self._terminal, self._rotulo_atual = indice, terminal, rotulo_atual
        self.update()

    def paintEvent(self, _evento) -> None:  # noqa: N802
        t = tema.t
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        n = len(self.etapas)
        if n == 0:
            return
        faixa = self.width() / n
        raio = 9
        y = 18
        fonte = QFont(self.font())
        fonte.setPointSizeF(8.5)
        p.setFont(fonte)
        for i, (_, nome) in enumerate(self.etapas):
            cx = faixa * i + faixa / 2
            feito = self._indice > i and not self._terminal
            atual = self._indice == i
            if self._terminal:
                cor = QColor(t["borda_forte"])
            elif feito or atual:
                cor = QColor(t["primaria"])
            else:
                cor = QColor(t["borda_forte"])
            if i < n - 1:
                proxima = faixa * (i + 1) + faixa / 2
                p.setPen(QPen(QColor(t["primaria"] if feito else t["borda"]), 2))
                p.drawLine(QPointF(cx + raio + 2, y), QPointF(proxima - raio - 2, y))
            p.setPen(Qt.PenStyle.NoPen)
            if atual and not self._terminal:
                halo = QColor(t["primaria"])
                halo.setAlphaF(0.22)
                p.setBrush(halo)
                p.drawEllipse(QPointF(cx, y), raio + 5, raio + 5)
            p.setBrush(cor if (feito or atual) and not self._terminal else QColor(t["superficie"]))
            p.setPen(QPen(cor, 2))
            p.drawEllipse(QPointF(cx, y), raio, raio)
            if feito:
                p.setPen(QPen(QColor(t["sobre_primaria"]), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                p.drawPolyline([QPointF(cx - 4, y), QPointF(cx - 1, y + 3), QPointF(cx + 4, y - 3)])
            elif atual and not self._terminal:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(t["sobre_primaria"]))
                p.drawEllipse(QPointF(cx, y), 3, 3)
            texto = self._rotulo_atual if (atual and self._rotulo_atual and not self._terminal) else nome
            p.setPen(QColor(t["texto"] if (atual or feito) and not self._terminal else t["mudo"]))
            negrito = QFont(fonte)
            negrito.setBold(atual and not self._terminal)
            p.setFont(negrito)
            p.drawText(QRectF(faixa * i, y + raio + 8, faixa, 18), Qt.AlignmentFlag.AlignCenter, texto)
        if self._terminal:
            p.setFont(fonte)
            largura = p.fontMetrics().horizontalAdvance(self._terminal) + 22
            caixa = QRectF(self.width() - largura, 0, largura, 22)
            fundo = QColor(t["perigo_suave"])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(fundo)
            p.drawRoundedRect(caixa, 11, 11)
            p.setPen(QColor(t["perigo"]))
            negrito = QFont(fonte)
            negrito.setBold(True)
            p.setFont(negrito)
            p.drawText(caixa, Qt.AlignmentFlag.AlignCenter, self._terminal)


# ---------------------------------------------------------------------------------- itens editaveis
class TabelaItens(QTableWidget):
    """Itens do documento. Quantidade e valor unitario sao editaveis com duplo clique (se `editavel`);
    a ultima coluna traz o botao de remover. Emite `editado(item_id, quantidade, valor)` e `remover_pedido(item_id)`."""

    editado = Signal(int, str, str)
    remover_pedido = Signal(int)

    def __init__(self, colunas: list[tuple[str, str, str]], parent: QWidget | None = None) -> None:
        """colunas: (titulo, caminho do atributo, tipo) com tipo texto | num | quantidade | valor | total."""
        super().__init__(0, len(colunas) + 1, parent)
        self.colunas = colunas
        self._ids: list[int] = []
        self._editavel = False
        self._bloqueio = False
        self.setHorizontalHeaderLabels([c[0] for c in colunas] + [""])
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(40)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        cab = self.horizontalHeader()
        cab.setHighlightSections(False)
        cab.setMinimumSectionSize(48)
        for i, (_, _, tipo) in enumerate(colunas):
            if tipo == "texto":
                cab.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                cab.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(len(colunas), QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(len(colunas), 44)
        self.itemChanged.connect(self._ao_editar)
        self.setMinimumHeight(150)

    def definir(self, itens, editavel: bool, pode_remover: bool) -> None:
        self._bloqueio = True
        self._editavel = editavel
        self.setRowCount(0)
        self._ids = []
        for linha, item in enumerate(itens):
            self.insertRow(linha)
            self._ids.append(int(item.id))
            for coluna, (_, caminho, tipo) in enumerate(self.colunas):
                valor = valor_coluna(item, caminho)
                celula = QTableWidgetItem(format_value(valor))
                alinha = Qt.AlignmentFlag.AlignRight if tipo in ("num", "quantidade", "valor", "total") else Qt.AlignmentFlag.AlignLeft
                celula.setTextAlignment(alinha | Qt.AlignmentFlag.AlignVCenter)
                if not (editavel and tipo in ("quantidade", "valor")):
                    celula.setFlags(celula.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(linha, coluna, celula)
            if pode_remover:
                botao = Botao("", "icone", "lixeira")
                botao.setToolTip("Remover item")
                botao.clicked.connect(lambda _=False, i=int(item.id): self.remover_pedido.emit(i))
                self.setCellWidget(linha, len(self.colunas), botao)
        self._bloqueio = False

    def _ao_editar(self, celula: QTableWidgetItem) -> None:
        if self._bloqueio or not self._editavel:
            return
        linha = celula.row()
        tipos = [c[2] for c in self.colunas]
        if tipos[celula.column()] not in ("quantidade", "valor"):
            return
        quantidade = self.item(linha, tipos.index("quantidade")).text()
        valor = self.item(linha, tipos.index("valor")).text()
        self.editado.emit(self._ids[linha], quantidade, valor)


# ------------------------------------------------------------------------------------------ dialogos
class DialogoFormulario(QDialog):
    """Dialogo modal com um Formulario; `exec_dados()` devolve o dict ou None se cancelado."""

    def __init__(self, parent: QWidget, titulo: str, campos: list[Campo], texto_ok: str = "Salvar", descricao: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(460)
        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(24, 22, 24, 20)
        corpo.setSpacing(12)
        corpo.addWidget(rotulo(titulo, "secao"))
        if descricao:
            corpo.addWidget(rotulo(descricao, "mudo", quebra=True))
        self.formulario = Formulario(campos)
        self.formulario.preencher(None)
        corpo.addWidget(self.formulario)
        self.erro = rotulo("", "erro", quebra=True)
        self.erro.hide()
        corpo.addWidget(self.erro)
        rodape = QHBoxLayout()
        rodape.addStretch()
        cancelar = Botao("Cancelar", "fantasma")
        cancelar.clicked.connect(self.reject)
        self.ok = Botao(texto_ok, "primario", "ok")
        self.ok.clicked.connect(self._confirmar)
        self.ok.setDefault(True)
        rodape.addWidget(cancelar)
        rodape.addWidget(self.ok)
        corpo.addLayout(rodape)
        self._validador: Callable[[dict], None] | None = None

    def definir_validador(self, funcao: Callable[[dict], None]) -> None:
        """`funcao(dados)` pode levantar ValueError; a mensagem aparece no dialogo sem fechar."""
        self._validador = funcao

    def _confirmar(self) -> None:
        if self._validador:
            try:
                self._validador(self.formulario.valores())
            except Exception as exc:  # noqa: BLE001
                self.erro.setText(str(exc))
                self.erro.show()
                return
        self.accept()

    def exec_dados(self) -> dict | None:
        return self.formulario.valores() if self.exec() == QDialog.DialogCode.Accepted else None


class DialogoMotivo(QDialog):
    """Pede um motivo obrigatorio (recusa/cancelamento). `pedir()` devolve o texto ou None."""

    def __init__(self, parent: QWidget, titulo: str, pergunta: str, texto_ok: str = "Confirmar") -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(440)
        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(24, 22, 24, 20)
        corpo.setSpacing(12)
        corpo.addWidget(rotulo(titulo, "secao"))
        corpo.addWidget(rotulo(pergunta, "mudo", quebra=True))
        self.texto = QPlainTextEdit()
        self.texto.setPlaceholderText("Descreva o motivo…")
        self.texto.setFixedHeight(90)
        corpo.addWidget(self.texto)
        self.erro = rotulo("O motivo é obrigatório.", "erro")
        self.erro.hide()
        corpo.addWidget(self.erro)
        rodape = QHBoxLayout()
        rodape.addStretch()
        voltar = Botao("Voltar", "fantasma")
        voltar.clicked.connect(self.reject)
        ok = Botao(texto_ok, "perigo", "alerta")
        ok.clicked.connect(self._confirmar)
        rodape.addWidget(voltar)
        rodape.addWidget(ok)
        corpo.addLayout(rodape)

    def _confirmar(self) -> None:
        if not self.texto.toPlainText().strip():
            self.erro.show()
            return
        self.accept()

    def pedir(self) -> str | None:
        return self.texto.toPlainText().strip() if self.exec() == QDialog.DialogCode.Accepted else None


def confirmar(parent: QWidget, titulo: str, texto: str, rotulo_ok: str = "Confirmar") -> bool:
    caixa = QMessageBox(parent)
    caixa.setWindowTitle(titulo)
    caixa.setText(texto)
    caixa.setIcon(QMessageBox.Icon.Question)
    ok = caixa.addButton(rotulo_ok, QMessageBox.ButtonRole.AcceptRole)
    caixa.addButton("Voltar", QMessageBox.ButtonRole.RejectRole)
    caixa.setDefaultButton(ok)
    caixa.exec()
    return caixa.clickedButton() is ok
