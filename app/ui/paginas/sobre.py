"""Tela Sobre: versao, ambiente, pastas do sistema e informacoes para o suporte."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QVBoxLayout

from app.controllers.sobre_controller import SobreController
from app.ui.componentes import Botao, Card, rotulo
from app.ui.paginas.base import Pagina


class PaginaSobre(Pagina):
    subtitulo = "Versão do sistema, onde ficam seus dados e informações para pedir ajuda."

    def __init__(self) -> None:
        super().__init__()
        self.controller = SobreController()
        self.info: dict = {}

        self.card_versao = Card()
        v = QVBoxLayout(self.card_versao)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(6)
        self.titulo_app = rotulo("", "secao")
        self.aviso = rotulo("", "mudo", quebra=True)
        v.addWidget(self.titulo_app)
        v.addWidget(self.aviso)
        self.corpo.addWidget(self.card_versao)

        self.card_dados = Card()
        d = QVBoxLayout(self.card_dados)
        d.setContentsMargins(20, 18, 20, 18)
        d.setSpacing(12)
        d.addWidget(rotulo("Detalhes", "secao"))
        self.grade = QGridLayout()
        self.grade.setHorizontalSpacing(24)
        self.grade.setVerticalSpacing(8)
        self.grade.setColumnStretch(1, 1)
        d.addLayout(self.grade)

        acoes = QHBoxLayout()
        acoes.setSpacing(8)
        self.botao_dados = Botao("Abrir pasta de dados", "secundario")
        self.botao_dados.clicked.connect(lambda: self._abrir("pasta_dados"))
        self.botao_logs = Botao("Abrir pasta de logs", "secundario")
        self.botao_logs.clicked.connect(lambda: self._abrir("pasta_logs"))
        self.botao_copiar = Botao("Copiar informações para o suporte", "primario")
        self.botao_copiar.clicked.connect(self.copiar_para_suporte)
        acoes.addWidget(self.botao_dados)
        acoes.addWidget(self.botao_logs)
        acoes.addStretch()
        acoes.addWidget(self.botao_copiar)
        d.addLayout(acoes)
        d.addWidget(
            rotulo(
                "O texto copiado traz versão, ambiente e caminhos das pastas. Não inclui senhas, dados de clientes nem o conteúdo dos logs.",
                "mudo",
                quebra=True,
            )
        )
        self.corpo.addWidget(self.card_dados)
        self.corpo.addStretch()
        self.recarregar()

    def ao_abrir(self) -> None:
        self.recarregar()

    def recarregar(self) -> None:
        self.info = self.controller.informacoes()
        i = self.info
        self.titulo_app.setText(f"{i['nome']} · versão {i['versao']}")
        self.aviso.setText(i["aviso"])
        while self.grade.count():
            item = self.grade.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        linhas = [
            ("Modo de execução", i["modo"]),
            ("Sistema operacional", i["sistema"]),
            ("Python / PySide6 / Qt", f"{i['python']} / {i['pyside']} / {i['qt']}"),
            ("SQLite", i["sqlite"]),
            ("Pasta de dados", str(i["pasta_dados"])),
            ("Banco de dados", f"{i['banco']}  ({i['tamanho_banco']}, schema {i['versao_banco']})"),
            ("Pasta de logs", str(i["pasta_logs"])),
            ("Pasta de backups", str(i["pasta_backups"])),
            ("Último backup", f"{i['ultimo_backup']} · automático {i['backup_automatico']}"),
        ]
        for n, (nome, valor) in enumerate(linhas):
            esquerda = rotulo(nome, "mudo")
            direita = rotulo(valor, "", quebra=True)
            direita.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.grade.addWidget(esquerda, n, 0, Qt.AlignmentFlag.AlignTop)
            self.grade.addWidget(direita, n, 1)

    def _abrir(self, chave: str) -> None:
        pasta = Path(str(self.info.get(chave, "")))
        try:
            pasta.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        if not pasta.exists() or not QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta))):
            self.avisar(f"Não foi possível abrir a pasta: {pasta}", "perigo")

    def copiar_para_suporte(self) -> None:
        QApplication.clipboard().setText(self.controller.texto_suporte())
        self.avisar("Informações copiadas. Cole na mensagem para o suporte.", "sucesso")
