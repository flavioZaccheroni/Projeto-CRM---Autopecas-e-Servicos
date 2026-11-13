"""Tela Sobre: versao, ambiente, pastas do sistema e informacoes para o suporte."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout

from app.controllers.sobre_controller import SobreController
from app.services.licenca_service import LicencaInvalida
from app.ui.componentes import Botao, Card, rotulo
from app.ui.paginas.base import Pagina
from app.utils.sessao import PermissaoNegada


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

        self.card_licenca = Card()
        lic = QVBoxLayout(self.card_licenca)
        lic.setContentsMargins(20, 18, 20, 18)
        lic.setSpacing(8)
        lic.addWidget(rotulo("Licença", "secao"))
        self.licenca_titulo = rotulo("", "")
        self.licenca_detalhe = rotulo("", "mudo", quebra=True)
        self.licenca_maquina = rotulo("", "mudo", quebra=True)
        self.licenca_maquina.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        for w in (self.licenca_titulo, self.licenca_detalhe, self.licenca_maquina):
            lic.addWidget(w)
        linha_lic = QHBoxLayout()
        self.botao_ativar = Botao("Ativar licença…", "primario")
        self.botao_ativar.clicked.connect(self.escolher_licenca)
        self.botao_codigo = Botao("Copiar código do computador", "secundario")
        self.botao_codigo.clicked.connect(self.copiar_codigo)
        linha_lic.addWidget(self.botao_ativar)
        linha_lic.addWidget(self.botao_codigo)
        linha_lic.addStretch()
        lic.addLayout(linha_lic)
        self.corpo.addWidget(self.card_licenca)

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
        self.licenca_titulo.setText(i.get("licenca_titulo", "Situação indisponível"))
        detalhe = i.get("licenca_detalhe", "")
        if i.get("licenca_erro"):
            detalhe = f"{detalhe}\nProblema com o arquivo de licença: {i['licenca_erro']}"
        self.licenca_detalhe.setText(detalhe)
        self.licenca_maquina.setText(
            f"Código deste computador: {i.get('codigo_maquina', '-')} (informe ao fornecedor se a licença for vinculada ao computador)"
        )
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

    def escolher_licenca(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(self, "Escolha o arquivo de licença", "", "Licença (*.erplic);;Todos os arquivos (*)")
        if caminho:
            self.ativar_arquivo(caminho)

    def ativar_arquivo(self, caminho: str) -> bool:
        try:
            situacao = self.controller.ativar_licenca(caminho)
        except (LicencaInvalida, PermissaoNegada) as exc:
            self.avisar(str(exc), "perigo")
            return False
        self.avisar(f"Licença ativada: {situacao.titulo}.", "sucesso")
        self.recarregar()
        janela = self.window()
        lateral = getattr(janela, "lateral", None)
        if lateral is not None and hasattr(lateral, "atualizar_licenca"):
            lateral.atualizar_licenca()
        return True

    def copiar_codigo(self) -> None:
        QApplication.clipboard().setText(str(self.info.get("codigo_maquina", "")))
        self.avisar("Código do computador copiado.", "sucesso")

    def copiar_para_suporte(self) -> None:
        QApplication.clipboard().setText(self.controller.texto_suporte())
        self.avisar("Informações copiadas. Cole na mensagem para o suporte.", "sucesso")
