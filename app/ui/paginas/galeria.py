"""Galeria de componentes: vitrine do sistema de design (cores, botoes, campos, KPIs, tabela, avisos, icones)."""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from app.ui import icones
from app.ui.componentes import Botao, Card, Coluna, Emblema, EstadoVazio, KpiCard, Seletor, TabelaDados, rotulo
from app.ui.paginas.base import Pagina
from app.ui.tema import TOKENS, ao_mudar_tema, cor_do_tom, tema


def _moeda(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _secao(titulo: str, descricao: str = "") -> tuple[Card, QVBoxLayout]:
    card = Card()
    corpo = QVBoxLayout(card)
    corpo.setContentsMargins(20, 18, 20, 20)
    corpo.setSpacing(12)
    corpo.addWidget(rotulo(titulo, "secao"))
    if descricao:
        corpo.addWidget(rotulo(descricao, "mudo", quebra=True))
    return card, corpo


class PaginaGaleria(Pagina):
    subtitulo = "Sistema de design — componentes, cores e ícones"

    def __init__(self) -> None:
        super().__init__()
        self.corpo.setContentsMargins(0, 0, 0, 0)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        conteudo = QWidget()
        pilha = QVBoxLayout(conteudo)
        pilha.setContentsMargins(28, 24, 28, 28)
        pilha.setSpacing(18)
        rolagem.setWidget(conteudo)
        self.corpo.addWidget(rolagem)

        self._kpis = self._secao_kpis(pilha)
        self._secao_cores(pilha)
        self._secao_botoes(pilha)
        self._secao_campos(pilha)
        self._secao_tabela(pilha)
        self._secao_estados(pilha)
        self._secao_icones(pilha)
        pilha.addStretch()
        ao_mudar_tema(self, self._recolorir)

    # ---- secoes
    def _secao_kpis(self, pilha: QVBoxLayout) -> list[tuple[KpiCard, float]]:
        grade = QHBoxLayout()
        grade.setSpacing(16)
        itens = [
            ("Faturamento do mês", "tendencia", "primaria", 48250.9, "↑ 12,4% sobre o mês anterior"),
            ("Ordens em aberto", "chave", "info", 7, "3 aguardando peça"),
            ("Contas a pagar vencidas", "alerta", "perigo", 3180.0, "2 títulos em atraso"),
            ("Saldo em caixa", "carteira", "sucesso", 15720.35, "Entradas menos saídas"),
        ]
        registro: list[tuple[KpiCard, float]] = []
        for titulo, icone, tom, valor, nota in itens:
            kpi = KpiCard(titulo, icone, tom, nota)
            kpi.tornar_clicavel()
            kpi.clicado.connect(lambda t=titulo: self.avisar(f"Abriria o detalhe de “{t}”.", "info"))
            grade.addWidget(kpi)
            registro.append((kpi, valor))
        pilha.addLayout(grade)
        return registro

    def ao_abrir(self) -> None:
        for kpi, valor in self._kpis:
            kpi.animar_para(valor, _moeda if valor > 100 else (lambda v: f"{v:.0f}"))

    def _secao_cores(self, pilha: QVBoxLayout) -> None:
        card, corpo = _secao("Cores semânticas", "Tokens do tema atual; alterne claro/escuro no cabeçalho.")
        grade = QHBoxLayout()
        grade.setSpacing(10)
        self._amostras: list[tuple[QLabel, str]] = []
        for tom in ("primaria", "sucesso", "aviso", "perigo", "info", "neutro"):
            amostra = QLabel(tom.capitalize())
            amostra.setAlignment(Qt.AlignmentFlag.AlignCenter)
            amostra.setMinimumHeight(54)
            self._amostras.append((amostra, tom))
            grade.addWidget(amostra)
        corpo.addLayout(grade)
        self._recolorir()
        pilha.addWidget(card)

    def _recolorir(self) -> None:
        for amostra, tom in self._amostras:
            forte, suave = cor_do_tom(tema.t, tom)
            amostra.setStyleSheet(f"background: {suave}; color: {forte}; border-radius: 10px; font-weight: 700;")

    def _secao_botoes(self, pilha: QVBoxLayout) -> None:
        card, corpo = _secao("Botões", "Primário para a ação principal; perigo para ações destrutivas; ícone/fantasma para ações discretas.")
        linha = QHBoxLayout()
        linha.setSpacing(10)
        for texto, variante, icone in (
            ("Salvar", "primario", "ok"),
            ("Novo registro", "primario", "mais"),
            ("Exportar", "secundario", "baixar"),
            ("Cancelar", "fantasma", None),
            ("Excluir", "perigo", "lixeira"),
        ):
            botao = Botao(texto, variante, icone)
            botao.clicked.connect(lambda _=False, t=texto: self.avisar(f"Clicou em “{t}”.", "sucesso" if t == "Salvar" else "info"))
            linha.addWidget(botao)
        desabilitado = Botao("Desabilitado", "primario")
        desabilitado.setEnabled(False)
        linha.addWidget(desabilitado)
        for icone in ("editar", "atualizar", "olho"):
            linha.addWidget(Botao("", "icone", icone))
        linha.addStretch()
        corpo.addLayout(linha)
        pilha.addWidget(card)

    def _secao_campos(self, pilha: QVBoxLayout) -> None:
        card, corpo = _secao("Campos e seletor", "O seletor filtra enquanto você digita e devolve só o ID (ex.: “2 - Maria”).")
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(8)
        seletor = Seletor(lambda: [(1, "João Almeida"), (2, "Maria Santos"), (3, "Carlos Pereira"), (4, "Ana Souza")], "Cliente…")
        saida = rotulo("ID escolhido: —", "mudo")
        seletor.escolhido.connect(lambda o: saida.setText(f"ID escolhido: {o[0]}" if o else "ID escolhido: —"))
        invalido = QLineEdit("123.456")
        invalido.setProperty("invalido", True)
        desabilitado = QLineEdit("Somente leitura")
        desabilitado.setEnabled(False)
        grade.addWidget(rotulo("Cliente (seletor)", "rotulo"), 0, 0)
        grade.addWidget(rotulo("Campo normal", "rotulo"), 0, 1)
        grade.addWidget(rotulo("Campo inválido", "rotulo"), 0, 2)
        grade.addWidget(rotulo("Desabilitado", "rotulo"), 0, 3)
        grade.addWidget(seletor, 1, 0)
        grade.addWidget(QLineEdit("Texto digitado"), 1, 1)
        grade.addWidget(invalido, 1, 2)
        grade.addWidget(desabilitado, 1, 3)
        grade.addWidget(saida, 2, 0)
        grade.addWidget(rotulo("CPF inválido", "erro"), 2, 2)
        corpo.addLayout(grade)
        corpo.addWidget(QCheckBox("Cliente ativo"))
        linha = QHBoxLayout()
        for texto, tom in (("FINALIZADA", "sucesso"), ("ORÇAMENTO", "info"), ("APROVADO", "primaria"), ("ATRASADO", "perigo"), ("PENDENTE", "aviso"), ("CANCELADA", "neutro")):
            linha.addWidget(Emblema(texto, tom))
        linha.addStretch()
        corpo.addLayout(linha)
        pilha.addWidget(card)

    def _secao_tabela(self, pilha: QVBoxLayout) -> None:
        card, corpo = _secao("Tabela de dados", "Clique no cabeçalho para ordenar (números e datas ordenam pelo valor real), digite para filtrar (sem acento) e use Ctrl+F.")
        tons = {"FINALIZADA": "sucesso", "ORCAMENTO": "info", "APROVADO": "primaria", "CANCELADA": "neutro", "RECUSADO": "perigo"}
        self.tabela = TabelaDados(
            [
                Coluna("ID", "num", 60),
                Coluna("Número", "texto", 110),
                Coluna("Cliente", "texto", 200),
                Coluna("Data", "data", 110),
                Coluna("Status", "emblema", 140, tons),
                Coluna("Valor", "num", 120),
            ],
            placeholder="Buscar vendas…",
        )
        nomes = ["João Almeida", "Maria Santos", "Carlos Pereira", "Ana Souza", "Pedro Lima", "Fernanda Costa", "Rafael Rocha"]
        rnd = random.Random(7)
        linhas = []
        for i in range(1, 41):
            status = rnd.choice(list(tons))
            linhas.append((i, [i, f"V{i:06d}", rnd.choice(nomes), date.today() - timedelta(days=rnd.randint(0, 120)), status, Decimal(rnd.randint(4000, 90000)) / 100]))
        self.tabela.definir_dados(linhas)
        self.tabela.setMinimumHeight(360)
        exportar = Botao("Exportar CSV", "secundario", "baixar")
        exportar.clicked.connect(lambda: self.avisar("Exportaria os registros visíveis em CSV.", "info"))
        self.tabela.adicionar_acao(exportar)
        self.tabela.ativado.connect(lambda iid: self.avisar(f"Abriria o registro {iid}.", "info"))
        corpo.addWidget(self.tabela)
        pilha.addWidget(card)

    def _secao_estados(self, pilha: QVBoxLayout) -> None:
        linha = QHBoxLayout()
        linha.setSpacing(16)
        card, corpo = _secao("Estado vazio", "Listas sem dados orientam a próxima ação.")
        vazio = EstadoVazio("Nenhum cliente cadastrado", "Cadastre o primeiro cliente para começar a registrar vendas e ordens de serviço.", "usuarios")
        vazio.definir_acao("Novo cliente", lambda: self.avisar("Abriria o cadastro de cliente.", "info"))
        corpo.addWidget(vazio)
        linha.addWidget(card)
        card2, corpo2 = _secao("Avisos", "Notificações temporárias, empilhadas no canto inferior direito.")
        botoes = QHBoxLayout()
        for texto, tom in (("Sucesso", "sucesso"), ("Informação", "info"), ("Atenção", "aviso"), ("Erro", "perigo")):
            botao = Botao(texto)
            botao.clicked.connect(lambda _=False, t=texto, k=tom: self.avisar(f"{t}: operação de exemplo concluída.", k))
            botoes.addWidget(botao)
        corpo2.addLayout(botoes)
        corpo2.addStretch()
        linha.addWidget(card2)
        pilha.addLayout(linha)

    def _secao_icones(self, pilha: QVBoxLayout) -> None:
        card, corpo = _secao("Ícones", f"{len(icones.nomes())} ícones SVG vetoriais, nítidos em qualquer escala e na cor do tema.")
        grade = QGridLayout()
        grade.setSpacing(6)
        self._icones: list[tuple[QLabel, str]] = []
        for indice, nome in enumerate(icones.nomes()):
            celula = QVBoxLayout()
            figura = QLabel()
            figura.setAlignment(Qt.AlignmentFlag.AlignCenter)
            texto = rotulo(nome, "mudo")
            texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            celula.addWidget(figura)
            celula.addWidget(texto)
            contenedor = QWidget()
            contenedor.setLayout(celula)
            self._icones.append((figura, nome))
            grade.addWidget(contenedor, indice // 9, indice % 9)
        corpo.addLayout(grade)
        pilha.addWidget(card)
        self._pintar_icones()
        ao_mudar_tema(self, self._pintar_icones)

    def _pintar_icones(self) -> None:
        for figura, nome in self._icones:
            figura.setPixmap(icones.pixmap(nome, tema.t["texto2"], 22))

    def focar_busca(self) -> bool:
        return self.tabela.focar_busca()


__all__ = ["PaginaGaleria", "TOKENS"]
