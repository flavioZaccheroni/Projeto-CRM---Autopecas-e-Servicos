"""Ciclo de vida da aplicacao Qt: login -> janela principal -> sair -> login."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.controllers.auth_controller import AuthController
from app.ui.login import JanelaLogin
from app.ui.paginas import fabricas_de_paginas
from app.ui.shell import JanelaPrincipal
from app.ui.tema import preparar_aplicacao


class Aplicacao:
    def __init__(self, argv: list[str] | None = None) -> None:
        self.app = QApplication.instance() or QApplication(argv or sys.argv)
        preparar_aplicacao(self.app)
        self.app.setApplicationName("ERP CRM Autopecas")
        self.login: JanelaLogin | None = None
        self.principal: JanelaPrincipal | None = None

    def mostrar_login(self) -> None:
        self.login = JanelaLogin()
        self.login.autenticado.connect(self._abrir_principal)
        self.login.show()

    def _abrir_principal(self, usuario) -> None:
        self.principal = JanelaPrincipal(usuario, fabricas_de_paginas(usuario))
        self.principal.sair_solicitado.connect(self._sair)
        self.principal.show()
        if self.login:
            self.login.close()

    def _sair(self) -> None:
        AuthController().encerrar_sessao()
        if self.principal:
            self.principal.close()
            self.principal = None
        self.mostrar_login()

    def executar(self) -> int:
        self.mostrar_login()
        return self.app.exec()
