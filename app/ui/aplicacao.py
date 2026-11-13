"""Ciclo de vida da aplicacao Qt: login -> janela principal -> sair -> login."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from app.controllers.auth_controller import AuthController
from app.controllers.licenca_controller import LicencaController
from app.controllers.seguranca_controller import SegurancaController
from app.ui.login import JanelaLogin
from app.ui.paginas import fabricas_de_paginas
from app.ui.shell import JanelaPrincipal
from app.ui.tema import preparar_aplicacao

logger = logging.getLogger(__name__)


class Aplicacao:
    def __init__(self, argv: list[str] | None = None) -> None:
        self.app = QApplication.instance() or QApplication(argv or sys.argv)
        preparar_aplicacao(self.app)
        self.app.setApplicationName("ERP CRM Autopecas")
        self.login: JanelaLogin | None = None
        self.principal: JanelaPrincipal | None = None
        self.app.aboutToQuit.connect(lambda: self._rotina_backup("sair"))

    def _rotina_backup(self, motivo: str) -> None:
        """Backup automatico ao abrir (1x/dia) e ao sair (se houve alteracoes). Nunca deve impedir o uso do sistema."""
        try:
            resultado = SegurancaController().executar_backup_automatico(motivo)
            situacao = SegurancaController().situacao_backup()
        except Exception:  # noqa: BLE001 - falha de backup nao pode derrubar o programa
            logger.exception("Falha no backup automatico (%s)", motivo)
            if motivo == "abrir" and self.principal:
                self.principal.avisos.mostrar("Não foi possível criar o backup automático. Verifique a pasta de backups.", "perigo")
            return
        if motivo != "abrir" or not self.principal:
            return
        if resultado.get("aviso"):
            self.principal.avisos.mostrar(f"Backup criado, mas a cópia extra falhou: {resultado['aviso']}", "perigo")
        dias = situacao["dias"]
        if situacao["auto"] is False and (dias is None or dias >= situacao["alerta_dias"]):
            texto = "Nenhum backup foi feito ainda." if dias is None else f"Faz {dias} dias sem backup."
            self.principal.avisos.mostrar(f"{texto} O backup automático está desligado (Configurações).", "perigo")

    def _verificar_licenca(self) -> None:
        """Aplica o modo somente consulta (teste/licenca vencidos) e avisa o usuario. Nunca impede abrir o sistema."""
        try:
            situacao = LicencaController().aplicar_restricao()
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao verificar a licenca")
            return
        if self.principal and situacao.precisa_aviso:
            self.principal.avisos.mostrar(f"{situacao.detalhe} Veja Sistema → Sobre para ativar a licença.", "perigo" if situacao.somente_consulta else "aviso", 9000)

    def mostrar_login(self) -> None:
        self.login = JanelaLogin()
        self.login.autenticado.connect(self._abrir_principal)
        self.login.show()

    def _abrir_principal(self, usuario) -> None:
        self.principal = JanelaPrincipal(usuario, fabricas_de_paginas(usuario))
        self.principal.sair_solicitado.connect(self._sair)
        self.principal.show()
        self._rotina_backup("abrir")
        self._verificar_licenca()
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
