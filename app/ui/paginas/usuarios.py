"""Administracao de acesso: Usuarios (lista + painel lateral) e Permissoes (matriz por perfil)."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QMessageBox, QScrollArea, QVBoxLayout, QWidget

from app.controllers.usuario_controller import PermissaoController, UsuarioController
from app.services.permissao_service import PERFIL_ADMIN
from app.ui.componentes import Botao, Card, Coluna, TabelaDados, rotulo
from app.ui.formulario import Campo, Formulario
from app.ui.operacoes import DialogoFormulario
from app.ui.paginas.base import Pagina
from app.ui.paginas.cadastros import PainelEdicao
from app.utils.sessao import ACOES, MODULOS, Sessao

TONS_USUARIO = {"Ativo": "sucesso", "Inativo": "neutro", "Bloqueado": "perigo"}


def situacao_usuario(usuario, agora: datetime | None = None) -> str:
    agora = agora or datetime.now()
    bloqueio = getattr(usuario, "bloqueado_ate", None)
    if bloqueio is not None and bloqueio > agora:
        return "Bloqueado"
    return "Ativo" if usuario.ativo else "Inativo"


class PaginaUsuarios(Pagina):
    subtitulo = "Quem acessa o sistema e com qual perfil. Senhas novas ou redefinidas exigem troca no primeiro login."

    def __init__(self, usuario) -> None:
        super().__init__()
        self.eu = usuario
        self.controller = UsuarioController()
        self.usuarios: dict[str, object] = {}
        self.perfis: dict[str, int] = {}
        self._id_atual: str | None = None
        self._sujo = False
        self.corpo.setContentsMargins(0, 0, 0, 0)
        raiz = QHBoxLayout()
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(16)
        self.corpo.addLayout(raiz)

        card = Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        self.tabela = TabelaDados(
            [Coluna("ID", "num", 50), Coluna("Nome", "texto", 220), Coluna("Login", "texto", 110), Coluna("Perfil", "texto", 120), Coluna("Situação", "emblema", 100, TONS_USUARIO)],
            vazio_titulo="Nenhum usuário",
            vazio_texto="Crie o primeiro usuário com o botão “Novo usuário”.",
            placeholder="Buscar usuários…",
        )
        self.botao_novo = Botao("Novo usuário", "primario", "mais")
        self.botao_novo.clicked.connect(self.novo)
        self.botao_novo.setEnabled(Sessao.pode("usuarios", "criar"))
        self.tabela.adicionar_acao(self.botao_novo)
        self.tabela.selecionado.connect(self._ao_selecionar)
        lay.addWidget(self.tabela)
        raiz.addWidget(card, 1)

        self.painel = PainelEdicao(380)
        interno = Card()
        interno.setMinimumWidth(380)
        interno.setMaximumWidth(380)
        v = QVBoxLayout(interno)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(12)
        topo = QHBoxLayout()
        self.titulo_painel = rotulo("", "secao")
        fechar = Botao("", "icone", "fechar")
        fechar.clicked.connect(self.cancelar)
        topo.addWidget(self.titulo_painel, 1)
        topo.addWidget(fechar)
        v.addLayout(topo)
        self.formulario = Formulario(
            [
                Campo("nome", "Nome"),
                Campo("login", "Login", metade=True),
                Campo("perfil", "Perfil", "lista", [], somente_lista=True, metade=True),
                Campo("email", "E-mail"),
                Campo("senha", "Senha inicial", "senha", dica="Mínimo 8, com letras e números"),
                Campo("ativo", "Usuário ativo", "bool"),
            ]
        )
        self.formulario.alterado.connect(self._marcar_sujo)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        rolagem.setWidget(self.formulario)
        v.addWidget(rolagem, 1)
        self.aviso_bloqueio = rotulo("", "erro", quebra=True)
        self.aviso_bloqueio.hide()
        v.addWidget(self.aviso_bloqueio)
        self.erro = rotulo("", "erro", quebra=True)
        self.erro.hide()
        v.addWidget(self.erro)
        extras = QHBoxLayout()
        self.botao_senha = Botao("Redefinir senha", "secundario", "cadeado")
        self.botao_senha.clicked.connect(self.redefinir_senha)
        self.botao_desbloquear = Botao("Desbloquear", "secundario", "ok")
        self.botao_desbloquear.clicked.connect(self.desbloquear)
        extras.addWidget(self.botao_senha)
        extras.addWidget(self.botao_desbloquear)
        v.addLayout(extras)
        rodape = QHBoxLayout()
        rodape.addStretch()
        cancelar = Botao("Cancelar", "fantasma")
        cancelar.clicked.connect(self.cancelar)
        self.botao_salvar = Botao("Salvar", "primario", "ok")
        self.botao_salvar.clicked.connect(self.salvar)
        rodape.addWidget(cancelar)
        rodape.addWidget(self.botao_salvar)
        v.addLayout(rodape)
        lp = QVBoxLayout(self.painel)
        lp.setContentsMargins(0, 0, 0, 0)
        lp.addWidget(interno)
        raiz.addWidget(self.painel)
        for atalho, funcao in (("Ctrl+N", self.novo), ("Ctrl+S", self.salvar), ("Esc", self.cancelar)):
            QShortcut(QKeySequence(atalho), self, activated=funcao).setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.recarregar(avisar=False)

    def focar_busca(self) -> bool:
        return self.tabela.focar_busca()

    def recarregar(self, avisar: bool = True) -> None:
        try:
            perfis = self.controller.listar_perfis()
            usuarios = self.controller.listar()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.perfis = {p.nome: p.id for p in perfis if p.ativo}
        combo = self.formulario.widgets["perfil"]
        atual = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(list(self.perfis))
        combo.setCurrentText(atual)
        combo.blockSignals(False)
        self.usuarios = {str(u.id): u for u in usuarios}
        self.tabela.definir_dados([(str(u.id), [u.id, u.nome, u.login, u.perfil.nome, situacao_usuario(u)]) for u in usuarios])

    # ---- fluxo
    def novo(self) -> None:
        if not Sessao.pode("usuarios", "criar"):
            self.avisar("Seu perfil não pode criar usuários.", "aviso")
            return
        if not self._descartar():
            return
        self.tabela.tabela.clearSelection()
        self._abrir(None)

    def _ao_selecionar(self, iid) -> None:
        if iid is None or str(iid) == self._id_atual:
            return
        if not self._descartar():
            if self._id_atual:
                self.tabela.selecionar(self._id_atual)
            return
        self._abrir(str(iid))

    def _abrir(self, iid: str | None) -> None:
        self._id_atual = iid
        u = self.usuarios.get(iid) if iid else None
        self.formulario.preencher(None if u is None else {"nome": u.nome, "login": u.login, "email": u.email, "perfil": u.perfil.nome, "ativo": u.ativo, "senha": ""})
        self._sujo = False
        self._mostrar_erro("")
        editando = u is not None
        self.titulo_painel.setText("Editar usuário" if editando else "Novo usuário")
        self.formulario.widgets["login"].setEnabled(not editando)  # o login nao muda depois de criado
        self.formulario.widgets["senha"].setVisible(not editando)
        self._rotulo_visivel(self.formulario.widgets["senha"], not editando)
        pode = Sessao.pode("usuarios", "editar" if editando else "criar")
        for nome in ("nome", "email", "perfil", "ativo"):
            self.formulario.widgets[nome].setEnabled(pode)
        self.botao_salvar.setEnabled(pode)
        self.botao_senha.setVisible(editando)
        self.botao_desbloquear.setVisible(editando)
        self.botao_senha.setEnabled(editando and Sessao.pode("usuarios", "editar"))
        bloqueado = editando and situacao_usuario(u) == "Bloqueado"
        self.botao_desbloquear.setEnabled(bloqueado and Sessao.pode("usuarios", "editar"))
        self.aviso_bloqueio.setVisible(bloqueado)
        if bloqueado:
            self.aviso_bloqueio.setText(f"Conta bloqueada por tentativas de login até {u.bloqueado_ate:%d/%m/%Y %H:%M}.")
        self.painel.abrir()
        if pode:
            (self.formulario.widgets["nome"]).setFocus()

    def _rotulo_visivel(self, widget: QWidget, visivel: bool) -> None:
        """Esconde/mostra o rotulo que fica na celula acima do campo (grade do Formulario)."""
        grade = self.formulario.layout()
        indice = grade.indexOf(widget)
        if indice < 0:
            return
        linha, coluna, _, _ = grade.getItemPosition(indice)
        rotulo_item = grade.itemAtPosition(linha - 1, coluna)
        if rotulo_item is not None and rotulo_item.widget() is not None:
            rotulo_item.widget().setVisible(visivel)

    def cancelar(self) -> None:
        if not self.painel.aberto or not self._descartar():
            return
        self._id_atual = None
        self.tabela.tabela.clearSelection()
        self.painel.fechar()

    def _marcar_sujo(self) -> None:
        self._sujo = True

    def _descartar(self) -> bool:
        if not (self._sujo and self.painel.aberto):
            return True
        r = QMessageBox.question(self, "Alterações não salvas", "Há alterações não salvas. Descartar?", QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        return r == QMessageBox.StandardButton.Discard

    def _mostrar_erro(self, texto: str) -> None:
        self.erro.setText(texto)
        self.erro.setVisible(bool(texto))

    def _perfil_id(self, nome: str) -> int:
        if nome not in self.perfis:
            raise ValueError("Selecione o perfil.")
        return self.perfis[nome]

    def salvar(self) -> None:
        if not self.painel.aberto or not self.botao_salvar.isEnabled():
            return
        d = self.formulario.valores()
        try:
            if self._id_atual is None:
                u = self.controller.criar(d["nome"], d["email"], d["login"], d["senha"], self._perfil_id(d["perfil"]))
                mensagem = "Usuário criado. Ele precisará trocar a senha no primeiro acesso."
            else:
                u = self.controller.atualizar(int(self._id_atual), d["nome"], d["email"], self._perfil_id(d["perfil"]), d["ativo"])
                mensagem = "Usuário atualizado."
        except Exception as exc:  # noqa: BLE001
            self._mostrar_erro(str(exc))
            return
        self._sujo = False
        self.recarregar(avisar=False)
        self.tabela.selecionar(str(u.id))
        self._abrir(str(u.id))
        self.avisar(mensagem, "sucesso")

    def redefinir_senha(self) -> None:
        if self._id_atual is None:
            return
        dlg = DialogoFormulario(self, "Redefinir senha", [Campo("senha", "Nova senha temporária", "senha", dica="Mínimo 8, com letras e números")], "Redefinir", "O usuário precisará trocá-la no próximo login.")
        dados = dlg.exec_dados()
        if dados is None:
            return
        if self.executar(lambda: self.controller.redefinir_senha(int(self._id_atual), dados["senha"]), "Senha redefinida. O usuário deverá trocá-la no próximo login."):
            self.recarregar(avisar=False)

    def desbloquear(self) -> None:
        if self._id_atual is None:
            return
        if self.executar(lambda: self.controller.desbloquear(int(self._id_atual)), "Conta desbloqueada."):
            iid = self._id_atual
            self.recarregar(avisar=False)
            self.tabela.selecionar(iid)
            self._sujo = False
            self._abrir(iid)


# ----------------------------------------------------------------------------- permissoes
GRUPOS_MODULOS: list[tuple[str, list[str]]] = [
    ("Cadastros", ["clientes", "veiculos", "fornecedores", "categorias", "marcas", "produtos"]),
    ("Operação", ["estoque", "compras", "vendas", "os", "financeiro", "relatorios"]),
    ("Sistema", ["seguranca", "usuarios", "permissoes", "configuracoes"]),
]
NOMES_MODULOS = {
    "clientes": "Clientes", "veiculos": "Veículos", "fornecedores": "Fornecedores", "categorias": "Categorias", "marcas": "Marcas", "produtos": "Produtos",
    "estoque": "Estoque", "compras": "Compras", "vendas": "Vendas", "os": "Ordem de serviço", "financeiro": "Financeiro", "relatorios": "Relatórios",
    "seguranca": "Segurança e backup", "usuarios": "Usuários", "permissoes": "Permissões", "configuracoes": "Configurações",
}
NOMES_ACOES = {"ver": "Ver", "criar": "Criar", "editar": "Editar", "excluir": "Excluir/cancelar"}


class MatrizPermissoes(QWidget):
    """Grade modulo x acao. Regra de coerencia: criar/editar/excluir exigem 'ver'; desmarcar 'ver' limpa o resto.
    Os cabecalhos de coluna e o 'tudo' de cada linha marcam/desmarcam em bloco."""

    alterado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.checks: dict[tuple[str, str], QCheckBox] = {}
        self.linha_todos: dict[str, QCheckBox] = {}
        self.coluna_todos: dict[str, QCheckBox] = {}
        self._silencio = False
        g = QGridLayout(self)
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(0)
        g.setVerticalSpacing(0)
        g.addWidget(rotulo("Módulo", "rotulo"), 0, 0)
        for c, acao in enumerate(ACOES, start=1):
            marca = QCheckBox(NOMES_ACOES[acao])
            marca.setToolTip(f"Marcar/desmarcar “{NOMES_ACOES[acao]}” em todos os módulos")
            marca.clicked.connect(lambda estado, a=acao: self._coluna(a, estado))
            self.coluna_todos[acao] = marca
            g.addWidget(marca, 0, c, Qt.AlignmentFlag.AlignCenter)
        g.addWidget(rotulo("Tudo", "rotulo"), 0, len(ACOES) + 1, Qt.AlignmentFlag.AlignCenter)
        linha = 1
        for grupo, modulos in GRUPOS_MODULOS:
            titulo = rotulo(grupo.upper(), "rotulo")
            titulo.setContentsMargins(0, 14, 0, 4)
            g.addWidget(titulo, linha, 0, 1, len(ACOES) + 2)
            linha += 1
            for modulo in modulos:
                nome = rotulo(NOMES_MODULOS.get(modulo, MODULOS.get(modulo, modulo)), "rotulo")
                nome.setMinimumHeight(34)
                g.addWidget(nome, linha, 0)
                for c, acao in enumerate(ACOES, start=1):
                    ck = QCheckBox()
                    ck.clicked.connect(lambda estado, m=modulo, a=acao: self._clique(m, a, estado))
                    self.checks[(modulo, acao)] = ck
                    g.addWidget(ck, linha, c, Qt.AlignmentFlag.AlignCenter)
                todos = QCheckBox()
                todos.setToolTip("Marcar/desmarcar tudo neste módulo")
                todos.clicked.connect(lambda estado, m=modulo: self._linha(m, estado))
                self.linha_todos[modulo] = todos
                g.addWidget(todos, linha, len(ACOES) + 1, Qt.AlignmentFlag.AlignCenter)
                linha += 1
        g.setColumnStretch(0, 1)
        for c in range(1, len(ACOES) + 2):
            g.setColumnMinimumWidth(c, 110)

    # ---- regras
    def _clique(self, modulo: str, acao: str, estado: bool) -> None:
        if acao == "ver" and not estado:
            for a in ACOES:
                self.checks[(modulo, a)].setChecked(False)
        elif acao != "ver" and estado:
            self.checks[(modulo, "ver")].setChecked(True)
        self._reflexo()

    def _linha(self, modulo: str, estado: bool) -> None:
        for a in ACOES:
            self.checks[(modulo, a)].setChecked(estado)
        self._reflexo()

    def _coluna(self, acao: str, estado: bool) -> None:
        for modulo in {m for m, _ in self.checks}:
            self.checks[(modulo, acao)].setChecked(estado)
            if estado and acao != "ver":
                self.checks[(modulo, "ver")].setChecked(True)
            if not estado and acao == "ver":
                for a in ACOES:
                    self.checks[(modulo, a)].setChecked(False)
        self._reflexo()

    def _reflexo(self) -> None:
        """Atualiza os 'tudo' de linha/coluna e avisa que mudou."""
        for modulo, todos in self.linha_todos.items():
            todos.setChecked(all(self.checks[(modulo, a)].isChecked() for a in ACOES))
        for acao, marca in self.coluna_todos.items():
            marca.setChecked(all(self.checks[(m, acao)].isChecked() for m in self.linha_todos))
        if not self._silencio:
            self.alterado.emit()

    # ---- dados
    def carregar(self, matriz: dict[str, set[str]]) -> None:
        self._silencio = True
        for (modulo, acao), ck in self.checks.items():
            ck.setChecked(acao in matriz.get(modulo, set()))
        self._reflexo()
        self._silencio = False

    def valores(self) -> dict[str, set[str]]:
        return {m: {a for a in ACOES if self.checks[(m, a)].isChecked()} for m in self.linha_todos}

    def somente_leitura(self, ativo: bool) -> None:
        for ck in [*self.checks.values(), *self.linha_todos.values(), *self.coluna_todos.values()]:
            ck.setEnabled(not ativo)


class PaginaPermissoes(Pagina):
    subtitulo = "O que cada perfil pode ver, criar, editar e excluir em cada módulo."

    def __init__(self, usuario) -> None:
        super().__init__()
        self.controller = PermissaoController()
        self.perfis: dict[str, int] = {}
        self._perfil: str = ""
        self._sujo = False
        topo = QHBoxLayout()
        topo.setSpacing(10)
        topo.addWidget(rotulo("Perfil", "rotulo"))
        self.combo = QComboBox()
        self.combo.setMinimumWidth(240)
        self.combo.activated.connect(self._trocar)
        topo.addWidget(self.combo)
        self.botao_novo = Botao("Novo perfil", "secundario", "mais")
        self.botao_novo.clicked.connect(self.novo_perfil)
        self.botao_novo.setEnabled(Sessao.pode("permissoes", "criar"))
        topo.addWidget(self.botao_novo)
        topo.addStretch()
        self.indicador = rotulo("", "mudo")
        topo.addWidget(self.indicador)
        self.botao_descartar = Botao("Descartar", "fantasma")
        self.botao_descartar.clicked.connect(self._recarregar_matriz)
        self.botao_salvar = Botao("Salvar permissões", "primario", "ok")
        self.botao_salvar.clicked.connect(self.salvar)
        topo.addWidget(self.botao_descartar)
        topo.addWidget(self.botao_salvar)
        self.corpo.addLayout(topo)
        self.aviso = rotulo("", "mudo", quebra=True)
        self.corpo.addWidget(self.aviso)
        card = Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 14, 20, 20)
        self.matriz = MatrizPermissoes()
        self.matriz.alterado.connect(self._marcar_sujo)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        rolagem.setWidget(self.matriz)
        lay.addWidget(rolagem)
        self.corpo.addWidget(card, 1)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.salvar).setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.recarregar(avisar=False)

    def recarregar(self, avisar: bool = True) -> None:
        try:
            perfis = self.controller.listar_perfis()
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.perfis = {p.nome: p.id for p in perfis}
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(list(self.perfis))
        if self.perfis:
            if self._perfil not in self.perfis:
                self._perfil = next(iter(self.perfis))
            self.combo.setCurrentText(self._perfil)
        self.combo.blockSignals(False)
        self._recarregar_matriz()

    def _recarregar_matriz(self) -> None:
        if self._perfil not in self.perfis:
            return
        try:
            dados = self.controller.carregar(self.perfis[self._perfil])
        except Exception as exc:  # noqa: BLE001
            self.avisar(str(exc), "perigo")
            return
        self.matriz.carregar(dados)
        self._sujo = False
        admin = self._perfil == PERFIL_ADMIN
        pode_editar = Sessao.pode("permissoes", "editar") and not admin
        self.matriz.somente_leitura(not pode_editar)
        mensagem = "O perfil Administrador tem acesso total e não pode ser alterado." if admin else "" if pode_editar else "Seu perfil só pode consultar as permissões."
        self.aviso.setText(mensagem)
        self.aviso.setVisible(bool(mensagem))
        self._atualizar_botoes()

    def _marcar_sujo(self) -> None:
        self._sujo = True
        self._atualizar_botoes()

    def _atualizar_botoes(self) -> None:
        editavel = self._perfil != PERFIL_ADMIN and Sessao.pode("permissoes", "editar")
        self.botao_salvar.setEnabled(editavel and self._sujo)
        self.botao_descartar.setEnabled(editavel and self._sujo)
        self.indicador.setText("Alterações não salvas" if self._sujo else "")

    def _trocar(self, _indice: int) -> None:
        novo = self.combo.currentText()
        if novo == self._perfil:
            return
        if self._sujo:
            r = QMessageBox.question(self, "Alterações não salvas", "Há alterações não salvas neste perfil. Descartar?", QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
            if r != QMessageBox.StandardButton.Discard:
                self.combo.setCurrentText(self._perfil)
                return
        self._perfil = novo
        self._recarregar_matriz()

    def novo_perfil(self) -> None:
        dlg = DialogoFormulario(self, "Novo perfil", [Campo("nome", "Nome do perfil")], "Criar", "Depois de criar, marque as permissões e salve.")
        dados = dlg.exec_dados()
        if dados is None:
            return
        if self.executar(lambda: self.controller.criar_perfil(dados["nome"]), f"Perfil “{dados['nome'].strip()}” criado. Marque as permissões e salve."):
            self._perfil = dados["nome"].strip()
            self._sujo = False
            self.recarregar(avisar=False)

    def salvar(self) -> None:
        if not self.botao_salvar.isEnabled() or self._perfil not in self.perfis:
            return
        if self.executar(lambda: self.controller.salvar_matriz(self.perfis[self._perfil], self.matriz.valores()), "Permissões salvas. Valem a partir do próximo login dos usuários deste perfil."):
            self._sujo = False
            self._atualizar_botoes()


__all__ = ["PaginaUsuarios", "PaginaPermissoes", "MatrizPermissoes"]
