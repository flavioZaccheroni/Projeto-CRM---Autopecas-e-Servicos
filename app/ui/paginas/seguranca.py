"""Seguranca e backup (backups + linha do tempo da auditoria) e Configuracoes (dados da empresa e parametros)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPainter
from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from app.controllers.seguranca_controller import SegurancaController
from app.controllers.usuario_controller import UsuarioController
from app.ui.componentes import Botao, CaixaBusca, Card, Coluna, EstadoVazio, KpiCard, TabelaDados, rotulo
from app.ui.formulario import Campo, Formulario
from app.ui.operacoes import DialogoFormulario, confirmar
from app.ui.paginas.base import Pagina
from app.ui.tema import ao_mudar_tema, tema
from app.utils.busca import normalizar
from app.utils.sessao import Sessao

LIMITE_INICIAL = 150
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def tom_da_acao(acao: str) -> str:
    """Cor do ponto na linha do tempo conforme o tipo de acao registrada."""
    a = acao.upper()
    if any(k in a for k in ("CANCEL", "REMOV", "ESTORN", "RESTAUR", "RECUS", "EXCLU", "BLOQ")):
        return "perigo"
    if any(k in a for k in ("CRIAR", "ABRIR", "ADICION", "FINALIZ", "RECEB", "BAIXAR", "APROVAR")):
        return "sucesso"
    if any(k in a for k in ("EDIT", "SALVAR", "PERMISS", "SENHA", "ATUALIZ", "DESBLOQ")):
        return "info"
    if any(k in a for k in ("BACKUP", "IMPRIM")):
        return "primaria"
    return "neutro"


def rotulo_do_dia(dia: date, hoje: date | None = None) -> str:
    hoje = hoje or date.today()
    if dia == hoje:
        return "Hoje"
    if (hoje - dia).days == 1:
        return "Ontem"
    return f"{dia.day} de {MESES[dia.month - 1]} de {dia.year}"


class Ponto(QWidget):
    """Bolinha colorida + trilho vertical da linha do tempo."""

    def __init__(self, tom: str, ultimo: bool) -> None:
        super().__init__()
        self._tom, self._ultimo = tom, ultimo
        self.setFixedWidth(22)
        ao_mudar_tema(self, self.update)

    def paintEvent(self, _e) -> None:  # noqa: N802
        t = tema.t
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() / 2
        if not self._ultimo:
            p.setPen(QColor(t["borda"]))
            p.drawLine(QPointF(cx, 14), QPointF(cx, self.height()))
        cor = {"perigo": t["perigo"], "sucesso": t["sucesso"], "info": t["info"], "primaria": t["primaria"]}.get(self._tom, t["mudo"])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(cor))
        p.drawEllipse(QRectF(cx - 5, 5, 10, 10))


class LinhaDoTempo(QWidget):
    """Auditoria agrupada por dia, do mais recente ao mais antigo, com busca por qualquer palavra."""

    def __init__(self) -> None:
        super().__init__()
        self._eventos: list = []
        self._nomes: dict[int, str] = {}
        self._limite = LIMITE_INICIAL
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(10)
        barra = QHBoxLayout()
        self.busca = CaixaBusca("Buscar por usuário, ação, registro…")
        self.busca.textChanged.connect(self._reconstruir)
        self.contador = rotulo("", "mudo")
        barra.addWidget(self.busca)
        barra.addWidget(self.contador)
        barra.addStretch()
        raiz.addLayout(barra)
        self.rolagem = QScrollArea()
        self.rolagem.setWidgetResizable(True)
        self.rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        raiz.addWidget(self.rolagem, 1)

    def definir(self, eventos: list, nomes: dict[int, str] | None = None) -> None:
        self._nomes = nomes or {}
        self._eventos = sorted(eventos, key=lambda e: (e.criado_em, e.id), reverse=True)
        self._limite = LIMITE_INICIAL
        self._reconstruir()

    def _filtrados(self) -> list:
        palavras = normalizar(self.busca.text()).split()
        if not palavras:
            return self._eventos
        saida = []
        for e in self._eventos:
            texto = normalizar(f"{_quem(e, self._nomes)} {e.acao} {e.entidade} {e.entidade_id or ''} {e.detalhes or ''}")
            if all(p in texto for p in palavras):
                saida.append(e)
        return saida

    def _reconstruir(self, *_args) -> None:
        eventos = self._filtrados()
        self.contador.setText(f"{min(len(eventos), self._limite)} de {len(eventos)} evento(s)")
        conteudo = QWidget()
        v = QVBoxLayout(conteudo)
        v.setContentsMargins(4, 4, 12, 12)
        v.setSpacing(0)
        if not eventos:
            v.addWidget(EstadoVazio("Nenhum evento", "A auditoria registra criações, edições, cancelamentos e backups." if not self._eventos else "Nenhum evento combina com a busca.", "escudo"))
            self.rolagem.setWidget(conteudo)
            return
        visiveis = eventos[: self._limite]
        dia_atual: date | None = None
        for i, e in enumerate(visiveis):
            dia = e.criado_em.date()
            if dia != dia_atual:
                dia_atual = dia
                titulo = rotulo(rotulo_do_dia(dia).upper(), "rotulo")
                titulo.setContentsMargins(0, 12, 0, 6)
                v.addWidget(titulo)
            linha = QHBoxLayout()
            linha.setSpacing(8)
            proximo_mesmo_dia = i + 1 < len(visiveis) and visiveis[i + 1].criado_em.date() == dia
            linha.addWidget(Ponto(tom_da_acao(e.acao), not proximo_mesmo_dia))
            texto = QVBoxLayout()
            texto.setSpacing(0)
            cabeca = rotulo(f"{e.acao.replace('_', ' ').capitalize()} · {e.entidade}" + (f" #{e.entidade_id}" if e.entidade_id else ""), "rotulo")
            quando = rotulo(f"{e.criado_em:%H:%M} · {_quem(e, self._nomes)}", "mudo")
            texto.addWidget(cabeca)
            texto.addWidget(quando)
            if e.detalhes:
                texto.addWidget(rotulo(str(e.detalhes), "mudo", quebra=True))
            texto.setContentsMargins(0, 0, 0, 10)
            linha.addLayout(texto, 1)
            v.addLayout(linha)
        if len(eventos) > self._limite:
            mais = Botao(f"Mostrar mais {min(LIMITE_INICIAL, len(eventos) - self._limite)}", "secundario")
            mais.clicked.connect(self._mais)
            v.addWidget(mais, 0, Qt.AlignmentFlag.AlignLeft)
        v.addStretch()
        self.rolagem.setWidget(conteudo)

    def _mais(self) -> None:
        self._limite += LIMITE_INICIAL
        self._reconstruir()


def _quem(evento, nomes: dict[int, str] | None = None) -> str:
    """Nome de quem fez a acao ('Sistema' sem usuario; 'Usuario #id' se o nome nao for acessivel)."""
    if evento.usuario_id is None:
        return "Sistema"
    return (nomes or {}).get(evento.usuario_id) or f"Usuário #{evento.usuario_id}"


class PaginaSeguranca(Pagina):
    subtitulo = "Backups com restauração segura e o histórico de tudo que foi feito no sistema."

    def __init__(self, usuario) -> None:
        super().__init__()
        self.eu = usuario
        self.controller = SegurancaController()
        self.arquivos: dict[str, Path] = {}

        linha = QHBoxLayout()
        linha.setSpacing(16)
        self.kpi_backups = KpiCard("Backups", "escudo", "primaria", "Arquivos disponíveis")
        self.kpi_ultimo = KpiCard("Último backup", "baixar", "sucesso", "")
        self.kpi_eventos = KpiCard("Eventos de auditoria", "documento", "info", "Registrados no sistema")
        for k in (self.kpi_backups, self.kpi_ultimo, self.kpi_eventos):
            linha.addWidget(k, 1)
        self.corpo.addLayout(linha)

        card = Card()
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 8, 16, 16)
        self.abas = QTabWidget()
        self.tab_backup = TabelaDados(
            [Coluna("Arquivo", "texto", 320), Coluna("Criado em", "data", 140), Coluna("Tamanho", "texto", 100)],
            vazio_titulo="Nenhum backup ainda",
            vazio_texto="Crie o primeiro backup para poder restaurar o banco em caso de problema.",
            placeholder="Buscar backup…",
        )
        self.botao_criar = Botao("Criar backup", "primario", "baixar")
        self.botao_criar.clicked.connect(self.criar_backup)
        self.botao_criar.setEnabled(Sessao.pode("seguranca", "criar"))
        self.botao_restaurar = Botao("Restaurar…", "perigo", "atualizar")
        self.botao_restaurar.clicked.connect(self.restaurar)
        self.botao_pasta = Botao("Abrir pasta", "fantasma")
        self.botao_pasta.clicked.connect(self.abrir_pasta)
        for b in (self.botao_pasta, self.botao_restaurar, self.botao_criar):
            self.tab_backup.adicionar_acao(b)
        self.tab_backup.selecionado.connect(self._ao_selecionar)
        self.timeline = LinhaDoTempo()
        self.abas.addTab(self.tab_backup, "Backups")
        self.abas.addTab(self.timeline, "Auditoria")
        v.addWidget(self.abas)
        self.corpo.addWidget(card, 1)
        self._ao_selecionar(None)
        self.recarregar(avisar=False)

    def focar_busca(self) -> bool:
        atual = self.abas.currentWidget()
        if atual is self.timeline:
            self.timeline.busca.setFocus()
            return True
        return self.tab_backup.focar_busca()

    def recarregar(self, avisar: bool = True) -> None:
        try:
            backups = [Path(str(a)) for a in self.controller.listar_backups()]
            eventos = self.controller.listar_auditoria()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.arquivos = {}
        linhas = []
        info = []
        for caminho in backups:
            try:
                estado = caminho.stat()
                quando, tamanho = datetime.fromtimestamp(estado.st_mtime), estado.st_size
            except OSError:
                quando, tamanho = None, 0
            self.arquivos[str(caminho)] = caminho
            info.append(quando)
            linhas.append((str(caminho), [caminho.name, quando, f"{tamanho / 1024 / 1024:.1f} MB" if tamanho >= 1024 * 1024 else f"{tamanho / 1024:.0f} KB"]))
        self.tab_backup.definir_dados(linhas)
        recentes = [q for q in info if q]
        self.kpi_backups.definir_valor(str(len(backups)))
        if recentes:
            ultimo = max(recentes)
            self.kpi_ultimo.definir_valor(f"{ultimo:%d/%m/%Y}", f"às {ultimo:%H:%M}")
        else:
            self.kpi_ultimo.definir_valor("—", "Nenhum backup criado")
        self.kpi_eventos.definir_valor(str(len(eventos)))
        try:
            nomes = {u.id: u.nome for u in UsuarioController().listar()}
        except Exception:  # noqa: BLE001 - sem permissao em Usuarios: mostra "Usuario #id"
            nomes = {}
        self.timeline.definir(list(eventos), nomes)

    def _ao_selecionar(self, iid) -> None:
        self.botao_restaurar.setEnabled(iid is not None and Sessao.pode("seguranca", "excluir"))
        self.botao_pasta.setEnabled(True)

    def criar_backup(self) -> None:
        resultado: dict = {}
        if self.executar(lambda: resultado.update(arquivo=self.controller.criar_backup(usuario_id=self.eu.id))):
            self.recarregar(avisar=False)
            self.tab_backup.selecionar(str(resultado["arquivo"]))
            self.avisar(f"Backup criado: {Path(str(resultado['arquivo'])).name}", "sucesso")

    def restaurar(self) -> None:
        iid = self.tab_backup.iid_atual()
        if iid is None:
            return
        arquivo = self.arquivos[str(iid)]
        if not confirmar(
            self,
            "Restaurar backup",
            f"O banco atual será substituído por:\n{arquivo.name}\n\nUma cópia do estado atual (pre_restore_*) será guardada antes. "
            "Depois da restauração, reinicie o sistema.\n\nContinuar?",
            "Restaurar",
        ):
            return
        if self.executar(lambda: self.controller.restaurar_backup(str(arquivo), usuario_id=self.eu.id), "Backup restaurado. Reinicie o sistema para recarregar todas as conexões."):
            self.recarregar(avisar=False)

    def abrir_pasta(self) -> None:
        iid = self.tab_backup.iid_atual()
        alvo = self.arquivos[str(iid)].parent if iid is not None else (next(iter(self.arquivos.values())).parent if self.arquivos else None)
        if alvo is None:
            self.avisar("Ainda não há backups; crie o primeiro.", "info")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(alvo)))


# ---------------------------------------------------------------------------- configuracoes
CAMPOS_EMPRESA = [
    ("empresa.nome", "Nome da empresa", "Aparece no cabeçalho da impressão da OS"),
    ("empresa.cnpj", "CNPJ", ""),
    ("empresa.telefone", "Telefone", ""),
    ("empresa.cidade", "Cidade", ""),
    ("empresa.endereco", "Endereço", ""),
]


class PaginaConfiguracoes(Pagina):
    subtitulo = "Dados da empresa e parâmetros do sistema."

    def __init__(self, usuario) -> None:
        super().__init__()
        self.eu = usuario
        self.controller = SegurancaController()
        self.valores: dict[str, str] = {}
        self._sujo = False
        linha = QHBoxLayout()
        linha.setSpacing(16)

        empresa = Card()
        v = QVBoxLayout(empresa)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(12)
        v.addWidget(rotulo("Dados da empresa", "secao"))
        v.addWidget(rotulo("Usados nos documentos impressos (como o PDF da ordem de serviço).", "mudo", quebra=True))
        self.formulario = Formulario([Campo(chave, nome, dica=dica, metade=chave in ("empresa.cnpj", "empresa.telefone")) for chave, nome, dica in CAMPOS_EMPRESA])
        self.formulario.alterado.connect(self._marcar_sujo)
        v.addWidget(self.formulario)
        v.addStretch()
        rodape = QHBoxLayout()
        self.indicador = rotulo("", "mudo")
        rodape.addWidget(self.indicador)
        rodape.addStretch()
        self.botao_salvar = Botao("Salvar dados", "primario", "ok")
        self.botao_salvar.clicked.connect(self.salvar_empresa)
        rodape.addWidget(self.botao_salvar)
        v.addLayout(rodape)
        empresa.setMaximumWidth(460)
        linha.addWidget(empresa)

        todos = Card()
        t = QVBoxLayout(todos)
        t.setContentsMargins(16, 16, 16, 16)
        t.addWidget(rotulo("Todos os parâmetros", "secao"))
        self.tabela = TabelaDados(
            [Coluna("Chave", "texto", 200), Coluna("Valor", "texto", 280)],
            vazio_titulo="Nenhum parâmetro",
            vazio_texto="Salve os dados da empresa ou crie um parâmetro.",
            placeholder="Buscar parâmetro…",
        )
        self.botao_novo = Botao("Novo parâmetro", "secundario", "mais")
        self.botao_novo.clicked.connect(lambda: self.editar_parametro(None))
        self.tabela.adicionar_acao(self.botao_novo)
        self.tabela.ativado.connect(self.editar_parametro)
        t.addWidget(rotulo("Dê dois cliques em uma linha para editar o valor.", "mudo"))
        t.addWidget(self.tabela)
        linha.addWidget(todos, 1)
        self.corpo.addLayout(linha, 1)
        pode = Sessao.pode("configuracoes", "editar")
        self.botao_salvar.setEnabled(False)
        self.formulario.somente_leitura(not pode)
        self.botao_novo.setEnabled(pode)
        QShortcut_ctrl_s(self, self.salvar_empresa)
        self.recarregar(avisar=False)

    def focar_busca(self) -> bool:
        return self.tabela.focar_busca()

    def recarregar(self, avisar: bool = True) -> None:
        try:
            itens = self.controller.listar_configuracoes()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.valores = {i.chave: (i.valor or "") for i in itens}
        self.tabela.definir_dados([(i.chave, [i.chave, i.valor or ""]) for i in itens])
        self.formulario.preencher(self.valores)
        self._sujo = False
        self._atualizar()

    def _marcar_sujo(self) -> None:
        self._sujo = True
        self._atualizar()

    def _atualizar(self) -> None:
        self.botao_salvar.setEnabled(self._sujo and Sessao.pode("configuracoes", "editar"))
        self.indicador.setText("Alterações não salvas" if self._sujo else "")

    def salvar_empresa(self) -> None:
        if not self.botao_salvar.isEnabled():
            return
        novos = self.formulario.valores()
        alterados = {c: str(v).strip() for c, v in novos.items() if str(v).strip() != self.valores.get(c, "")}

        def _acao() -> None:
            for chave, valor in alterados.items():
                self.controller.salvar_configuracao(chave, valor, usuario_id=self.eu.id)

        if self.executar(_acao, "Dados da empresa salvos." if alterados else "Nada mudou."):
            self.recarregar(avisar=False)

    def editar_parametro(self, chave) -> None:
        novo = chave is None
        campos = [Campo("chave", "Chave", dica="ex.: empresa.site"), Campo("valor", "Valor")]
        dlg = DialogoFormulario(self, "Novo parâmetro" if novo else "Editar parâmetro", campos, "Salvar")
        if not novo:
            dlg.formulario.preencher({"chave": chave, "valor": self.valores.get(str(chave), "")})
            dlg.formulario.widgets["chave"].setEnabled(False)
        dados = dlg.exec_dados()
        if dados is None:
            return
        if self.executar(lambda: self.controller.salvar_configuracao(dados["chave"], dados["valor"], usuario_id=self.eu.id), "Parâmetro salvo."):
            self.recarregar(avisar=False)


def QShortcut_ctrl_s(pagina: QWidget, funcao) -> None:  # noqa: N802 - pequeno atalho local
    from PySide6.QtGui import QKeySequence, QShortcut

    QShortcut(QKeySequence("Ctrl+S"), pagina, activated=funcao).setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
