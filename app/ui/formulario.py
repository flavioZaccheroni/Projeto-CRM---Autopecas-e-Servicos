"""Formulario dirigido por especificacao: monta os campos, le/escreve valores e sinaliza alteracoes."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QDateEdit, QGridLayout, QLineEdit, QWidget

from app.ui.componentes import Seletor, rotulo


@dataclass
class Campo:
    nome: str
    rotulo: str
    tipo: str = "texto"  # texto | bool | lista | busca | data
    opcoes: list[str] = field(default_factory=list)  # tipo lista
    fonte: Callable[[], list] | None = None  # tipo busca: devolve [(id, nome)]
    somente_lista: bool = False  # lista: aceita so os valores das opcoes
    metade: bool = False  # ocupa meia largura (pares lado a lado)
    dica: str = ""
    padrao: str = ""  # valor inicial em registro novo (lista/texto)


class Formulario(QWidget):
    alterado = Signal()

    def __init__(self, campos: list[Campo], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.campos = campos
        self.widgets: dict[str, QWidget] = {}
        self._silencio = False
        grade = QGridLayout(self)
        grade.setContentsMargins(0, 0, 0, 0)
        grade.setHorizontalSpacing(12)
        grade.setVerticalSpacing(4)
        linha, coluna = 0, 0
        for campo in campos:
            widget = self._criar(campo)
            self.widgets[campo.nome] = widget
            if campo.tipo == "bool":
                if coluna:
                    linha, coluna = linha + 2, 0
                grade.addWidget(widget, linha, 0, 1, 2)
                linha += 2
                continue
            etiqueta = rotulo(campo.rotulo, "rotulo")
            if campo.metade:
                grade.addWidget(etiqueta, linha, coluna)
                grade.addWidget(widget, linha + 1, coluna)
                if coluna:
                    linha, coluna = linha + 2, 0
                else:
                    coluna = 1
            else:
                if coluna:
                    linha, coluna = linha + 2, 0
                grade.addWidget(etiqueta, linha, 0, 1, 2)
                grade.addWidget(widget, linha + 1, 0, 1, 2)
                linha += 2
        grade.setColumnStretch(0, 1)
        grade.setColumnStretch(1, 1)
        grade.setRowStretch(linha + 2, 1)  # sobra de altura vai para o fim, nao entre os campos

    def _criar(self, campo: Campo) -> QWidget:
        if campo.tipo == "bool":
            widget: QWidget = QCheckBox(campo.rotulo)
            widget.setChecked(True)
            widget.toggled.connect(self._mudou)
        elif campo.tipo == "data":
            widget = QDateEdit(QDate.currentDate())
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("dd/MM/yyyy")
            widget.dateChanged.connect(self._mudou)
        elif campo.tipo == "busca":
            widget = Seletor(campo.fonte, campo.dica or "Digite para buscar…")
            widget.currentTextChanged.connect(self._mudou)
        elif campo.tipo == "lista":
            widget = QComboBox()
            widget.setEditable(not campo.somente_lista)
            widget.addItems(["", *campo.opcoes] if not campo.somente_lista else campo.opcoes)
            widget.setCurrentIndex(-1 if campo.somente_lista else 0)
            widget.currentTextChanged.connect(self._mudou)
        else:
            widget = QLineEdit()
            if campo.dica:
                widget.setPlaceholderText(campo.dica)
            widget.textChanged.connect(self._mudou)
        return widget

    def _mudou(self, *_args) -> None:
        if not self._silencio:
            self.alterado.emit()
            self.limpar_erros()

    # ---- valores
    def valores(self) -> dict:
        dados: dict = {}
        for campo in self.campos:
            widget = self.widgets[campo.nome]
            if isinstance(widget, QCheckBox):
                dados[campo.nome] = widget.isChecked()
            elif isinstance(widget, QDateEdit):
                dados[campo.nome] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, Seletor):
                dados[campo.nome] = widget.id()
            elif isinstance(widget, QComboBox):
                dados[campo.nome] = widget.currentText()
            else:
                dados[campo.nome] = widget.text()  # type: ignore[attr-defined]
        return dados

    def preencher(self, origem) -> None:
        """`origem` pode ser um objeto (getattr) ou um dict; None limpa o formulario."""
        self._silencio = True
        try:
            for campo in self.campos:
                widget = self.widgets[campo.nome]
                if origem is None:
                    valor = True if campo.tipo == "bool" else campo.padrao
                elif isinstance(origem, dict):
                    valor = origem.get(campo.nome, "")
                else:
                    valor = getattr(origem, campo.nome, "")
                if valor is None:
                    valor = ""
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(valor))
                elif isinstance(widget, QDateEdit):
                    texto = str(valor)[:10] if valor else date.today().isoformat()
                    widget.setDate(QDate.fromString(texto, "yyyy-MM-dd"))
                elif isinstance(widget, Seletor):
                    widget.recarregar()
                    widget.definir_id(valor)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(valor))
                else:
                    widget.setText(str(valor))  # type: ignore[attr-defined]
        finally:
            self._silencio = False
        self.limpar_erros()

    def limpar_erros(self) -> None:
        for widget in self.widgets.values():
            if widget.property("invalido"):
                widget.setProperty("invalido", False)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

    def marcar_invalido(self, nome: str) -> None:
        widget = self.widgets.get(nome)
        if widget is not None:
            widget.setProperty("invalido", True)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def somente_leitura(self, ativo: bool) -> None:
        for widget in self.widgets.values():
            widget.setEnabled(not ativo)

    def primeiro_campo(self) -> QWidget | None:
        return next(iter(self.widgets.values()), None)
