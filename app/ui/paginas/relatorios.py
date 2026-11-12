"""Relatorios: escolha o tipo (cartoes) e o formato (PDF/Excel); abre o arquivo ou a pasta depois de gerar."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout

from app.controllers.relatorio_controller import RelatorioController
from app.ui import icones
from app.ui.componentes import Botao, Card, Coluna, TabelaDados, rotulo
from app.ui.paginas.base import Pagina
from app.ui.tema import ao_mudar_tema, tema
from app.utils.sessao import Sessao

TIPOS = [
    ("vendas", "Vendas", "recibo", "Número, cliente, status e valor de cada venda."),
    ("estoque", "Estoque", "estoque", "Produto, saldo e localização."),
    ("os", "Ordens de serviço", "chave", "Cliente, veículo, status e valor."),
    ("financeiro", "Financeiro", "carteira", "Lançamentos e movimentações de caixa."),
]


class CartaoTipo(QPushButton):
    def __init__(self, chave: str, titulo: str, icone: str, descricao: str) -> None:
        super().__init__()
        self.chave, self._icone = chave, icone
        self.setCheckable(True)
        self.setProperty("variante", "cartao")
        self.setMinimumHeight(96)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(4)
        self._figura = rotulo("")
        self._figura.setFixedSize(34, 34)
        self._figura.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        t = rotulo(titulo, "secao")
        d = rotulo(descricao, "mudo", quebra=True)
        for w in (t, d):
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        topo = QHBoxLayout()
        topo.addWidget(self._figura)
        topo.addWidget(t, 1)
        v.addLayout(topo)
        v.addWidget(d)
        self.toggled.connect(lambda _: self._pintar())
        ao_mudar_tema(self, self._pintar)
        self._pintar()

    def _pintar(self) -> None:
        tk = tema.t
        marcado = self.isChecked()
        self._figura.setStyleSheet(f"background: {tk['primaria_suave'] if marcado else tk['superficie2']}; border-radius: 9px;")
        self._figura.setPixmap(icones.pixmap(self._icone, tk["primaria"] if marcado else tk["texto2"], 18))
        self._figura.setAlignment(Qt.AlignmentFlag.AlignCenter)


class PaginaRelatorios(Pagina):
    subtitulo = "Exporte relatórios operacionais em PDF ou Excel."

    def __init__(self) -> None:
        super().__init__()
        self.controller = RelatorioController()
        self.tipo = "vendas"
        self.formato = "pdf"
        self.ultimo: Path | None = None

        grade = QGridLayout()
        grade.setSpacing(16)
        self.cartoes: dict[str, CartaoTipo] = {}
        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        for i, (chave, titulo, icone, desc) in enumerate(TIPOS):
            c = CartaoTipo(chave, titulo, icone, desc)
            c.clicked.connect(lambda _=False, k=chave: setattr(self, "tipo", k))
            c.setChecked(i == 0)
            grupo.addButton(c)
            self.cartoes[chave] = c
            grade.addWidget(c, 0, i)
        self.corpo.addLayout(grade)

        card = Card()
        v = QHBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)
        v.addWidget(rotulo("Formato", "rotulo"))
        self.btn_pdf, self.btn_xlsx = Botao("PDF", "filtro"), Botao("Excel (.xlsx)", "filtro")
        for b, f in ((self.btn_pdf, "pdf"), (self.btn_xlsx, "xlsx")):
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, x=f: setattr(self, "formato", x))
        self.btn_pdf.setChecked(True)
        g2 = QButtonGroup(self)
        g2.setExclusive(True)
        g2.addButton(self.btn_pdf)
        g2.addButton(self.btn_xlsx)
        v.addWidget(self.btn_pdf)
        v.addWidget(self.btn_xlsx)
        v.addStretch()
        self.botao_gerar = Botao("Gerar relatório", "primario", "baixar")
        self.botao_gerar.clicked.connect(self.gerar)
        self.botao_gerar.setEnabled(Sessao.pode("relatorios", "ver"))
        v.addWidget(self.botao_gerar)
        self.corpo.addWidget(card)

        hist = Card()
        h = QVBoxLayout(hist)
        h.setContentsMargins(16, 16, 16, 16)
        h.addWidget(rotulo("Gerados nesta sessão", "secao"))
        self.historico = TabelaDados(
            [Coluna("Hora", "texto", 80), Coluna("Relatório", "texto", 140), Coluna("Formato", "texto", 80), Coluna("Arquivo", "texto", 400)],
            vazio_titulo="Nada gerado ainda",
            vazio_texto="Escolha um tipo, o formato e clique em “Gerar relatório”.",
            placeholder="Buscar…",
        )
        self.historico.ativado.connect(self._abrir)
        self._arquivos: dict[str, Path] = {}
        self._linhas: list[tuple[object, list]] = []
        self.botao_abrir = Botao("Abrir arquivo", "secundario", "documento")
        self.botao_abrir.clicked.connect(lambda: self._abrir(self.historico.iid_atual() or (self._linhas[0][0] if self._linhas else None)))
        self.botao_pasta = Botao("Abrir pasta", "fantasma")
        self.botao_pasta.clicked.connect(self._abrir_pasta)
        self.historico.adicionar_acao(self.botao_pasta)
        self.historico.adicionar_acao(self.botao_abrir)
        h.addWidget(self.historico)
        self.corpo.addWidget(hist, 1)

    def gerar(self) -> None:
        resultado: dict = {}
        if not self.executar(lambda: resultado.update(arquivo=Path(str(self.controller.gerar(self.tipo, self.formato))))):
            return
        arquivo = resultado["arquivo"]
        iid = str(len(self._linhas) + 1)
        self._arquivos[iid] = arquivo
        nome = next(t[1] for t in TIPOS if t[0] == self.tipo)
        self._linhas.insert(0, (iid, [datetime.now().strftime("%H:%M:%S"), nome, self.formato.upper(), str(arquivo)]))
        self.historico.definir_dados(self._linhas)
        self.avisar(f"Relatório gerado: {arquivo.name}", "sucesso")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(arquivo)))

    def _abrir(self, iid) -> None:
        arquivo = self._arquivos.get(str(iid)) if iid is not None else None
        if arquivo is None:
            self.avisar("Gere ou selecione um relatório na lista.", "info")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(arquivo)))

    def _abrir_pasta(self) -> None:
        iid = self.historico.iid_atual() or (self._linhas[0][0] if self._linhas else None)
        arquivo = self._arquivos.get(str(iid)) if iid is not None else None
        if arquivo is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(arquivo.parent)))
