"""Spike: prova que PySide6 empacota com PyInstaller e abre. Nao faz parte do produto."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtSvg import QSvgRenderer  # noqa: F401  (icones SVG)
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView


def main() -> int:
    app = QApplication(sys.argv)
    janela = QMainWindow()
    modelo = QStandardItemModel(3, 2)
    for linha in range(3):
        modelo.setItem(linha, 0, QStandardItem(f"Item {linha}"))
        modelo.setItem(linha, 1, QStandardItem(str(linha * 10)))
    tabela = QTableView()
    tabela.setModel(modelo)
    tabela.setSortingEnabled(True)
    janela.setCentralWidget(tabela)
    janela.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, "--selftest" in sys.argv)
    janela.show()
    app.processEvents()
    if "--selftest" in sys.argv:
        print("OK pyside6 spike")
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
