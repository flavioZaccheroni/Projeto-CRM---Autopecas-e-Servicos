"""Login em tela dividida, com troca de senha obrigatoria (medidor de forca) e feedback visual de erro."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AVISO_DEMO
from app.controllers.auth_controller import AuthController
from app.controllers.licenca_controller import LicencaController
from app.ui import icones
from app.ui.componentes import Botao, rotulo
from app.ui.tema import ao_mudar_tema, tema


class PainelMarca(QWidget):
    """Lado esquerdo do login: gradiente, formas decorativas e os destaques do sistema."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumWidth(380)
        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(44, 48, 44, 40)
        corpo.setSpacing(14)
        marca = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: rgba(255,255,255,0.16); border-radius: 12px;")
        logo.setPixmap(icones.pixmap("chave", "#ffffff", 22))
        nome = QLabel("ERP Autopeças")
        nome.setStyleSheet("color: white; font-size: 18px; font-weight: 700;")
        marca.addWidget(logo)
        marca.addWidget(nome)
        marca.addStretch()
        corpo.addLayout(marca)
        corpo.addStretch(2)
        titulo = QLabel("Gestão completa para\nsua autopeça e oficina")
        titulo.setStyleSheet("color: white; font-size: 28px; font-weight: 700;")
        corpo.addWidget(titulo)
        corpo.addSpacing(10)
        for icone, texto in (
            ("recibo", "Orçamentos, vendas e ordens de serviço"),
            ("estoque", "Estoque sempre atualizado"),
            ("carteira", "Financeiro integrado e auditável"),
            ("escudo", "Perfis, permissões e backup seguro"),
        ):
            linha = QHBoxLayout()
            figura = QLabel()
            figura.setPixmap(icones.pixmap(icone, "#99f6e4", 18))
            descricao = QLabel(texto)
            descricao.setStyleSheet("color: rgba(255,255,255,0.88); font-size: 14px;")
            linha.addWidget(figura)
            linha.addWidget(descricao)
            linha.addStretch()
            corpo.addLayout(linha)
        corpo.addStretch(3)

    def paintEvent(self, _evento) -> None:  # noqa: N802
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradiente = QLinearGradient(0, 0, self.width(), self.height())
        gradiente.setColorAt(0.0, QColor("#0f766e"))
        gradiente.setColorAt(0.55, QColor("#115e59"))
        gradiente.setColorAt(1.0, QColor("#0f172a"))
        pintor.fillRect(self.rect(), gradiente)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(255, 255, 255, 14))
        pintor.drawEllipse(QPointF(self.width() * 0.95, self.height() * 0.12), 190, 190)
        pintor.setBrush(QColor(255, 255, 255, 10))
        pintor.drawEllipse(QPointF(self.width() * 0.05, self.height() * 0.95), 230, 230)
        pintor.setPen(QPen(QColor(255, 255, 255, 22), 1.2))
        pintor.setBrush(Qt.BrushStyle.NoBrush)
        pintor.drawEllipse(QRectF(self.width() * 0.55, self.height() * 0.55, 240, 240))


def forca_da_senha(senha: str) -> tuple[int, str]:
    """0-100 e o rotulo: considera tamanho, letras, numeros, maiusculas e simbolos."""
    pontos = 0
    pontos += 30 if len(senha) >= 8 else (15 if len(senha) >= 5 else 0)
    pontos += 20 if any(c.isalpha() for c in senha) else 0
    pontos += 20 if any(c.isdigit() for c in senha) else 0
    pontos += 15 if any(c.isupper() for c in senha) and any(c.islower() for c in senha) else 0
    pontos += 15 if any(not c.isalnum() for c in senha) else 0
    rotulo_forca = "Fraca" if pontos < 50 else ("Média" if pontos < 80 else "Forte")
    return pontos, rotulo_forca if senha else ""


class CampoSenha(QLineEdit):
    """Campo de senha com botao de mostrar/ocultar."""

    def __init__(self, placeholder: str = "") -> None:
        super().__init__()
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setPlaceholderText(placeholder)
        self._acao = QAction(self)
        self._acao.setToolTip("Mostrar/ocultar senha")
        self._acao.triggered.connect(self._alternar)
        self.addAction(self._acao, QLineEdit.ActionPosition.TrailingPosition)
        ao_mudar_tema(self, self._icone)
        self._icone()

    def _icone(self) -> None:
        oculto = self.echoMode() == QLineEdit.EchoMode.Password
        self._acao.setIcon(icones.icone("olho" if oculto else "olho_off", tema.t["mudo"], 18))

    def _alternar(self) -> None:
        oculto = self.echoMode() == QLineEdit.EchoMode.Password
        self.setEchoMode(QLineEdit.EchoMode.Normal if oculto else QLineEdit.EchoMode.Password)
        self._icone()


class DialogoTrocaSenha(QDialog):
    """Troca obrigatoria (primeiro acesso ou senha redefinida), com medidor de forca."""

    def __init__(self, parent: QWidget, controller: AuthController, usuario) -> None:
        super().__init__(parent)
        self.controller, self.usuario = controller, usuario
        self.setWindowTitle("Defina uma nova senha")
        self.setModal(True)
        self.setMinimumWidth(420)
        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(28, 26, 28, 24)
        corpo.setSpacing(6)
        corpo.addWidget(rotulo("Defina uma nova senha", "titulo"))
        corpo.addWidget(rotulo("Mínimo de 8 caracteres, com letras e números. Você precisa trocar a senha para continuar.", "subtitulo", quebra=True))
        corpo.addSpacing(10)
        self.atual = CampoSenha("Senha atual")
        self.nova = CampoSenha("Nova senha")
        self.confirmacao = CampoSenha("Confirmar nova senha")
        for titulo, campo in (("Senha atual", self.atual), ("Nova senha", self.nova)):
            corpo.addWidget(rotulo(titulo, "rotulo"))
            corpo.addWidget(campo)
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(6)
        self.barra.setRange(0, 100)
        self.forca = rotulo("", "mudo")
        corpo.addWidget(self.barra)
        corpo.addWidget(self.forca)
        corpo.addWidget(rotulo("Confirmar nova senha", "rotulo"))
        corpo.addWidget(self.confirmacao)
        self.erro = rotulo("", "erro", quebra=True)
        corpo.addWidget(self.erro)
        botoes = QHBoxLayout()
        botoes.addStretch()
        cancelar = Botao("Cancelar", "secundario")
        self.salvar = Botao("Salvar nova senha", "primario", "ok")
        self.salvar.setDefault(True)
        botoes.addWidget(cancelar)
        botoes.addWidget(self.salvar)
        corpo.addSpacing(8)
        corpo.addLayout(botoes)
        cancelar.clicked.connect(self.reject)
        self.salvar.clicked.connect(self._salvar)
        self.nova.textChanged.connect(self._medir)
        ao_mudar_tema(self, lambda: self._medir(self.nova.text()))
        self._medir("")

    def _medir(self, senha: str) -> None:
        pontos, texto = forca_da_senha(senha)
        cor = tema.t["perigo"] if pontos < 50 else (tema.t["aviso"] if pontos < 80 else tema.t["sucesso"])
        self.barra.setValue(pontos)
        self.barra.setStyleSheet(
            f"QProgressBar {{ background: {tema.t['borda']}; border-radius: 3px; border: none; }}"
            f"QProgressBar::chunk {{ background: {cor}; border-radius: 3px; }}"
        )
        self.forca.setText(f"Força da senha: {texto}" if texto else "")

    def _salvar(self) -> None:
        if self.nova.text() != self.confirmacao.text():
            self.erro.setText("A confirmação não confere com a nova senha.")
            return
        try:
            self.controller.trocar_senha(self.usuario.id, self.atual.text(), self.nova.text())
        except ValueError as exc:
            self.erro.setText(str(exc))
            return
        self.accept()


def _texto_licenca_atual() -> str:
    try:
        return LicencaController().situacao().detalhe
    except Exception:  # noqa: BLE001 - o login deve abrir mesmo sem banco/licenca legivel
        return AVISO_DEMO


class JanelaLogin(QWidget):
    autenticado = Signal(object)

    def __init__(self, controller: AuthController | None = None) -> None:
        super().__init__()
        self.controller = controller or AuthController()
        self.setWindowTitle("ERP CRM Autopeças & Serviços — Entrar")
        self.setObjectName("Raiz")
        self.resize(960, 600)
        self.setMinimumSize(860, 560)
        linha = QHBoxLayout(self)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(0)
        linha.addWidget(PainelMarca(), 5)

        lado = QWidget()
        lado.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lado_corpo = QVBoxLayout(lado)
        lado_corpo.setContentsMargins(40, 18, 40, 30)
        topo = QHBoxLayout()
        topo.addStretch()
        self.botao_tema = Botao("", "icone", "lua")
        self.botao_tema.clicked.connect(tema.alternar)
        topo.addWidget(self.botao_tema)
        lado_corpo.addLayout(topo)
        lado_corpo.addStretch(1)

        self.formulario = QFrame()
        form = QVBoxLayout(self.formulario)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        form.addWidget(rotulo("Bem-vindo de volta", "titulo"))
        form.addWidget(rotulo("Entre com suas credenciais para continuar.", "subtitulo"))
        form.addSpacing(18)
        form.addWidget(rotulo("Usuário", "rotulo"))
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText("seu.usuario")
        form.addWidget(self.usuario)
        form.addSpacing(6)
        form.addWidget(rotulo("Senha", "rotulo"))
        self.senha = CampoSenha("Sua senha")
        form.addWidget(self.senha)
        self.erro = rotulo("", "erro", quebra=True)
        self.erro.setMinimumHeight(34)
        form.addWidget(self.erro)
        self.entrar = Botao("Entrar", "primario", "direita")
        self.entrar.setMinimumHeight(42)
        self.entrar.setDefault(True)
        form.addWidget(self.entrar)
        lado_corpo.addWidget(self.formulario)
        lado_corpo.addStretch(2)
        lado_corpo.addWidget(rotulo("Atalho: Enter para entrar", "mudo"), 0, Qt.AlignmentFlag.AlignHCenter)
        self.aviso_demo = rotulo(_texto_licenca_atual(), "mudo", quebra=True)
        self.aviso_demo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lado_corpo.addWidget(self.aviso_demo)
        linha.addWidget(lado, 4)

        self.entrar.clicked.connect(self._entrar)
        self.usuario.returnPressed.connect(self.senha.setFocus)
        self.senha.returnPressed.connect(self._entrar)
        for campo in (self.usuario, self.senha):
            campo.textChanged.connect(self._limpar_erro)
        tema.mudou.connect(self._pintar)
        self._pintar()
        self.usuario.setFocus()

    def _pintar(self, *_args) -> None:
        self.botao_tema.definir_icone("sol" if tema.modo == "escuro" else "lua")

    def _limpar_erro(self) -> None:
        self.erro.setText("")
        for campo in (self.usuario, self.senha):
            if campo.property("invalido"):
                campo.setProperty("invalido", False)
                campo.style().unpolish(campo)
                campo.style().polish(campo)

    def _falha(self, mensagem: str) -> None:
        self.erro.setText(mensagem)
        for campo in (self.usuario, self.senha):
            campo.setProperty("invalido", True)
            campo.style().unpolish(campo)
            campo.style().polish(campo)
        self._tremer()
        self.entrar.setEnabled(True)
        self.entrar.setText("Entrar")

    def _tremer(self) -> None:
        origem = self.formulario.pos()
        animacao = QPropertyAnimation(self.formulario, b"pos", self)
        animacao.setDuration(360)
        for fracao, deslocamento in ((0.0, 0), (0.15, -10), (0.35, 9), (0.55, -7), (0.75, 5), (1.0, 0)):
            animacao.setKeyValueAt(fracao, origem + QPoint(deslocamento, 0))
        animacao.setEasingCurve(QEasingCurve.Type.OutQuad)
        animacao.start()
        self._animacao = animacao

    def _entrar(self) -> None:
        if not self.usuario.text().strip() or not self.senha.text():
            self._falha("Informe usuário e senha.")
            return
        self.entrar.setEnabled(False)
        self.entrar.setText("Entrando…")
        QTimer.singleShot(30, self._autenticar)  # deixa o botao repintar antes da verificacao (PBKDF2)

    def _autenticar(self) -> None:
        try:
            usuario = self.controller.autenticar(self.usuario.text(), self.senha.text())
        except ValueError as exc:  # conta bloqueada por tentativas
            self._falha(str(exc))
            return
        if usuario is None:
            self.senha.clear()
            self._falha("Usuário ou senha inválidos.")
            self.senha.setFocus()
            return
        if usuario.precisa_trocar_senha and DialogoTrocaSenha(self, self.controller, usuario).exec() != QDialog.DialogCode.Accepted:
            self.controller.encerrar_sessao()
            self.senha.clear()
            self.entrar.setEnabled(True)
            self.entrar.setText("Entrar")
            return
        self.entrar.setEnabled(True)
        self.entrar.setText("Entrar")
        self.senha.clear()
        self.autenticado.emit(usuario)
