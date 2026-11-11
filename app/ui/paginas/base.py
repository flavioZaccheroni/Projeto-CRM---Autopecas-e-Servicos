"""Base das paginas: margens padrao, titulo/subtitulo exibidos no cabecalho e ganchos (ao_abrir/recarregar/focar_busca)."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget


class Pagina(QWidget):
    subtitulo = ""

    def __init__(self) -> None:
        super().__init__()
        self.corpo = QVBoxLayout(self)
        self.corpo.setContentsMargins(28, 24, 28, 24)
        self.corpo.setSpacing(18)

    def ao_abrir(self) -> None:  # chamado a cada vez que a pagina e exibida
        pass

    def recarregar(self) -> None:
        pass

    def focar_busca(self) -> bool:
        return False

    def avisar(self, texto: str, tom: str = "info") -> None:
        janela = self.window()
        if hasattr(janela, "avisos"):
            janela.avisos.mostrar(texto, tom)
