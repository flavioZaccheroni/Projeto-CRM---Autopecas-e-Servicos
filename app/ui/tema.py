"""Sistema de design: tokens de cor (claro/escuro), tipografia e QSS gerado a partir dos tokens."""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

RAIO = 10
RAIO_PEQUENO = 8

TOKENS: dict[str, dict[str, str]] = {
    "claro": {
        "bg": "#f4f6fa", "superficie": "#ffffff", "superficie2": "#f1f5f9", "borda": "#e2e8f0", "borda_forte": "#cbd5e1",
        "texto": "#0f172a", "texto2": "#475569", "mudo": "#64748b",
        "primaria": "#0d9488", "primaria_hover": "#0f766e", "primaria_suave": "#ccfbf1", "sobre_primaria": "#ffffff",
        "perigo": "#dc2626", "perigo_suave": "#fee2e2", "aviso": "#d97706", "aviso_suave": "#fef3c7",
        "sucesso": "#16a34a", "sucesso_suave": "#dcfce7", "info": "#2563eb", "info_suave": "#dbeafe",
        "lateral": "#0f172a", "lateral_texto": "#cbd5e1", "lateral_mudo": "#64748b", "lateral_hover": "#1e293b",
        "lateral_ativo": "#0d9488", "sombra": "#0f172a",
    },
    "escuro": {
        "bg": "#0b1220", "superficie": "#111a2e", "superficie2": "#182339", "borda": "#233048", "borda_forte": "#33425e",
        "texto": "#e6eaf2", "texto2": "#b4bfd1", "mudo": "#8593ab",
        "primaria": "#2dd4bf", "primaria_hover": "#5eead4", "primaria_suave": "#0f3b3a", "sobre_primaria": "#04211f",
        "perigo": "#f87171", "perigo_suave": "#3b1a1d", "aviso": "#fbbf24", "aviso_suave": "#3a2c0f",
        "sucesso": "#4ade80", "sucesso_suave": "#10301d", "info": "#60a5fa", "info_suave": "#14284a",
        "lateral": "#070d19", "lateral_texto": "#c3cde0", "lateral_mudo": "#6b7a93", "lateral_hover": "#121c30",
        "lateral_ativo": "#14b8a6", "sombra": "#000000",
    },
}

TONS = ("neutro", "primaria", "sucesso", "aviso", "perigo", "info")


def cor_do_tom(tokens: dict[str, str], tom: str) -> tuple[str, str]:
    """(cor forte, cor suave) de um tom semantico."""
    mapa = {
        "primaria": ("primaria", "primaria_suave"),
        "sucesso": ("sucesso", "sucesso_suave"),
        "aviso": ("aviso", "aviso_suave"),
        "perigo": ("perigo", "perigo_suave"),
        "info": ("info", "info_suave"),
        "neutro": ("mudo", "superficie2"),
    }
    forte, suave = mapa.get(tom, mapa["neutro"])
    return tokens[forte], tokens[suave]


def _svg_para_qss(nome: str, corpo: str, cor: str) -> str:
    """Grava um SVG pequeno em arquivo temporario e devolve o caminho (QSS so aceita `url(arquivo)`)."""
    import tempfile
    from pathlib import Path

    pasta = Path(tempfile.gettempdir()) / "erp_autopecas_ui"
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / f"{nome}-{cor.lstrip('#')}.svg"
    if not arquivo.exists():
        arquivo.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{corpo}</svg>',
            encoding="utf-8",
        )
    return arquivo.as_posix()


def gerar_qss(t: dict[str, str]) -> str:
    marca = _svg_para_qss("marca", '<path d="M5 12.5l4.5 4.5L19 7.5"/>', t["sobre_primaria"])
    seta = _svg_para_qss("seta", '<path d="M6 9l6 6 6-6"/>', t["mudo"])
    return f"""
* {{ font-family: "Segoe UI Variable Text", "Segoe UI", "Inter", sans-serif; font-size: 13px; color: {t['texto']}; }}
QWidget {{ background: transparent; }}
QMainWindow, QDialog, #Raiz {{ background: {t['bg']}; }}
QToolTip {{ background: {t['lateral']}; color: #f8fafc; border: none; padding: 6px 8px; border-radius: 6px; }}

/* texto */
QLabel[papel="titulo"] {{ font-size: 22px; font-weight: 700; }}
QLabel[papel="subtitulo"] {{ color: {t['mudo']}; font-size: 13px; }}
QLabel[papel="secao"] {{ font-size: 14px; font-weight: 600; }}
QLabel[papel="mudo"] {{ color: {t['mudo']}; font-size: 12px; }}
QLabel[papel="erro"] {{ color: {t['perigo']}; font-size: 12px; }}
QLabel[papel="kpi"] {{ font-size: 26px; font-weight: 700; }}
QLabel[papel="rotulo"] {{ color: {t['texto2']}; font-size: 12px; font-weight: 600; }}

/* cartoes */
#Card {{ background: {t['superficie']}; border: 1px solid {t['borda']}; border-radius: {RAIO}px; }}
#Card[destaque="true"] {{ border: 1px solid {t['primaria']}; }}
#IconeKpi {{ border-radius: 12px; }}

/* botoes */
QPushButton {{ background: {t['superficie']}; border: 1px solid {t['borda_forte']}; border-radius: {RAIO_PEQUENO}px;
    padding: 8px 14px; font-weight: 600; }}
QPushButton:hover {{ background: {t['superficie2']}; }}
QPushButton:pressed {{ background: {t['borda']}; }}
QPushButton:disabled {{ color: {t['mudo']}; background: {t['superficie2']}; border-color: {t['borda']}; }}
QPushButton:focus {{ border: 1px solid {t['primaria']}; }}
QPushButton[variante="primario"] {{ background: {t['primaria']}; color: {t['sobre_primaria']}; border: 1px solid {t['primaria']}; }}
QPushButton[variante="primario"]:hover {{ background: {t['primaria_hover']}; border-color: {t['primaria_hover']}; }}
QPushButton[variante="primario"]:disabled {{ background: {t['borda_forte']}; color: {t['mudo']}; border-color: {t['borda_forte']}; }}
QPushButton[variante="perigo"] {{ background: {t['perigo_suave']}; color: {t['perigo']}; border: 1px solid transparent; }}
QPushButton[variante="perigo"]:disabled {{ background: {t['superficie2']}; color: {t['mudo']}; }}
QPushButton[variante="perigo"]:hover:enabled {{ background: {t['perigo']}; color: #ffffff; }}
QPushButton[variante="filtro"] {{ background: {t['superficie']}; border: 1px solid {t['borda_forte']}; border-radius: 15px; padding: 5px 14px; color: {t['texto2']}; font-weight: 600; }}
QPushButton[variante="filtro"]:hover {{ background: {t['superficie2']}; }}
QPushButton[variante="filtro"]:checked {{ background: {t['primaria_suave']}; border-color: {t['primaria']}; color: {t['primaria']}; }}
QPushButton[variante="cartao"] {{ background: {t['superficie']}; border: 1px solid {t['borda']}; border-radius: {RAIO}px; text-align: left; }}
QPushButton[variante="cartao"]:hover {{ border-color: {t['mudo']}; background: {t['superficie']}; }}
QPushButton[variante="cartao"]:checked {{ border: 2px solid {t['primaria']}; background: {t['superficie']}; }}
QPushButton[variante="fantasma"] {{ background: transparent; border: 1px solid transparent; color: {t['texto2']}; }}
QPushButton[variante="fantasma"]:hover {{ background: {t['superficie2']}; }}
QPushButton[variante="icone"] {{ padding: 7px; border: 1px solid transparent; background: transparent; }}
QPushButton[variante="icone"]:hover {{ background: {t['superficie2']}; }}

/* campos */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
    background: {t['superficie']}; border: 1px solid {t['borda_forte']}; border-radius: {RAIO_PEQUENO}px; padding: 8px 10px;
    selection-background-color: {t['primaria']}; selection-color: {t['sobre_primaria']}; }}
QLineEdit:hover, QComboBox:hover {{ border-color: {t['mudo']}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus {{ border: 1px solid {t['primaria']}; }}
QLineEdit[invalido="true"], QComboBox[invalido="true"] {{ border: 1px solid {t['perigo']}; }}
QLineEdit:disabled, QComboBox:disabled {{ background: {t['superficie2']}; color: {t['mudo']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url({seta}); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{ background: {t['superficie']}; border: 1px solid {t['borda_forte']}; border-radius: 8px; padding: 4px;
    selection-background-color: {t['primaria_suave']}; selection-color: {t['texto']}; outline: none; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid {t['borda_forte']}; background: {t['superficie']}; }}
QCheckBox::indicator:checked {{ background: {t['primaria']}; border-color: {t['primaria']}; image: url({marca}); }}

/* tabelas */
QTableView {{ background: {t['superficie']}; alternate-background-color: {t['superficie2']}; border: 1px solid {t['borda']};
    border-radius: {RAIO_PEQUENO}px; gridline-color: transparent; selection-background-color: {t['primaria_suave']}; selection-color: {t['texto']};
    outline: none; }}
QTableView::item {{ padding: 6px 10px; border: none; }}
QTableView::item:hover {{ background: {t['superficie2']}; }}
QTableView::item:selected {{ background: {t['primaria_suave']}; color: {t['texto']}; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{ background: {t['superficie']}; color: {t['mudo']}; font-weight: 600; font-size: 12px; padding: 9px 10px;
    border: none; border-bottom: 1px solid {t['borda']}; }}
QHeaderView::section:hover {{ color: {t['texto']}; }}
QTableCornerButton::section {{ background: {t['superficie']}; border: none; }}

/* rolagem */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t['borda_forte']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t['mudo']}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {t['borda_forte']}; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* menu e abas */
QMenu {{ background: {t['superficie']}; border: 1px solid {t['borda']}; border-radius: 8px; padding: 6px; }}
QMenu::item {{ padding: 8px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {t['primaria_suave']}; }}
QMenu::separator {{ height: 1px; background: {t['borda']}; margin: 4px 6px; }}
QTabBar::tab {{ background: transparent; padding: 9px 16px; border-bottom: 2px solid transparent; color: {t['mudo']}; font-weight: 600; }}
QTabBar::tab:selected {{ color: {t['primaria']}; border-bottom: 2px solid {t['primaria']}; }}
QTabBar::tab:hover {{ color: {t['texto']}; }}
QTabWidget::pane {{ border: none; }}

/* barra lateral */
#Lateral {{ background: {t['lateral']}; }}
#Lateral QLabel {{ color: {t['lateral_texto']}; }}
#Lateral QLabel[papel="marca"] {{ color: #ffffff; font-size: 16px; font-weight: 700; }}
#Lateral QLabel[papel="grupo"] {{ color: {t['lateral_mudo']}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
QPushButton[papel="nav"] {{ background: transparent; border: none; color: {t['lateral_texto']}; text-align: left; padding: 10px 12px;
    border-radius: 9px; font-weight: 500; }}
QPushButton[papel="nav"]:hover {{ background: {t['lateral_hover']}; color: #ffffff; }}
QPushButton[papel="nav"]:checked {{ background: {t['lateral_ativo']}; color: #ffffff; font-weight: 600; }}
#Lateral QPushButton[variante="icone"] {{ color: {t['lateral_texto']}; }}
#Lateral QPushButton[variante="icone"]:hover {{ background: {t['lateral_hover']}; }}

/* cabecalho */
#Cabecalho {{ background: {t['superficie']}; border-bottom: 1px solid {t['borda']}; }}
#Busca {{ background: {t['superficie2']}; border: 1px solid {t['borda']}; border-radius: 9px; padding: 8px 12px; color: {t['mudo']};
    text-align: left; font-weight: 400; }}
#Busca:hover {{ border-color: {t['borda_forte']}; }}
#Avatar {{ background: {t['primaria']}; color: {t['sobre_primaria']}; border-radius: 16px; font-weight: 700; }}

/* emblemas e avisos */
QLabel[papel="emblema"] {{ border-radius: 9px; padding: 2px 9px; font-size: 11px; font-weight: 700; }}
#Toast {{ background: {t['lateral']}; border-radius: 10px; }}
#Toast QLabel {{ color: #f8fafc; font-weight: 600; }}
#Paleta {{ background: {t['superficie']}; border: 1px solid {t['borda']}; border-radius: 14px; }}
#Paleta QLineEdit {{ border: none; border-bottom: 1px solid {t['borda']}; border-radius: 0; padding: 14px 16px; font-size: 15px; }}
#Paleta QListWidget {{ border: none; padding: 6px; outline: none; }}
#Paleta QListWidget::item {{ padding: 10px 12px; border-radius: 8px; }}
#Paleta QListWidget::item:selected {{ background: {t['primaria_suave']}; color: {t['texto']}; }}
"""


class GerenciadorTema(QObject):
    """Tema atual (claro/escuro), persistido entre execucoes."""

    mudou = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.modo = "claro"
        self._tokens = TOKENS["claro"]

    @property
    def t(self) -> dict[str, str]:
        return self._tokens

    def cor(self, nome: str) -> QColor:
        return QColor(self._tokens[nome])

    def carregar_preferencia(self) -> str:
        try:
            valor = QSettings("ErpAutopecas", "Interface").value("tema", "claro")
        except Exception:  # noqa: BLE001
            valor = "claro"
        return valor if valor in TOKENS else "claro"

    def aplicar(self, modo: str | None = None) -> None:
        self.modo = modo or self.modo
        self._tokens = TOKENS[self.modo]
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(gerar_qss(self._tokens))
        self.mudou.emit(self.modo)

    def alternar(self) -> None:
        self.aplicar("escuro" if self.modo == "claro" else "claro")
        try:
            QSettings("ErpAutopecas", "Interface").setValue("tema", self.modo)
        except Exception:  # noqa: BLE001
            pass


tema = GerenciadorTema()


def ao_mudar_tema(objeto: QObject, funcao) -> None:
    """Chama `funcao()` quando o tema muda e desconecta sozinho quando `objeto` e destruido
    (evita 'Internal C++ object already deleted' com conexoes por lambda)."""

    def _chamar(_modo: str) -> None:
        funcao()

    tema.mudou.connect(_chamar)
    objeto.destroyed.connect(lambda *_: _desconectar(_chamar))


def _desconectar(chamada) -> None:
    try:
        tema.mudou.disconnect(chamada)
    except (RuntimeError, TypeError):
        pass


def preparar_aplicacao(app: QApplication) -> None:
    """Fonte base e tema salvo. Chamar uma vez, logo apos criar o QApplication."""
    familias = set(QFontDatabase.families())
    for nome in ("Segoe UI Variable Text", "Segoe UI", "Inter"):
        if nome in familias:
            app.setFont(QFont(nome, 10))
            break
    tema.aplicar(tema.carregar_preferencia())
