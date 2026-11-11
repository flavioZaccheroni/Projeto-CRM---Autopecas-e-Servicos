"""Telas administrativas: Usuarios, Permissoes (perfis) e Configuracoes."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from app.controllers.seguranca_controller import SegurancaController
from app.controllers.usuario_controller import PermissaoController, UsuarioController
from app.services.permissao_service import PERFIL_ADMIN
from app.utils.sessao import ACOES, MODULOS
from app.views.helpers import aplicar_permissao, executar
from app.views.theme import format_value


def _cabecalho(frame, titulo: str, subtitulo: str) -> None:
    ttk.Label(frame, text=titulo, style="Header.TLabel").pack(anchor="w")
    ttk.Label(frame, text=subtitulo, style="Subtle.TLabel").pack(anchor="w", pady=(4, 12))


def _tabela(master, colunas: list[str], altura: int = 10) -> ttk.Treeview:
    frame = ttk.Frame(master, style="Surface.TFrame")
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=colunas, show="headings", height=altura)
    for coluna in colunas:
        tree.heading(coluna, text=coluna.replace("_", " ").title())
        tree.column(coluna, width=140, anchor="w")
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    return tree


class UsuariosFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = UsuarioController()
        self.vars = {n: tk.StringVar() for n in ("nome", "email", "login", "senha", "perfil")}
        self.ativo = tk.BooleanVar(value=True)
        self.perfis: dict[str, int] = {}
        self.selecionado: int | None = None

        _cabecalho(self, "Usuarios", "Cadastre usuarios e atribua perfis. Novos usuarios e senhas redefinidas exigem troca no primeiro login.")
        form = ttk.LabelFrame(self, text="Dados do usuario", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        campos = [("nome", "Nome"), ("email", "E-mail"), ("login", "Login"), ("senha", "Senha inicial")]
        for i, (nome, rotulo) in enumerate(campos):
            ttk.Label(form, text=rotulo).grid(row=i // 2, column=(i % 2) * 2, padx=(0, 6), pady=3, sticky="w")
            ttk.Entry(form, textvariable=self.vars[nome], width=28, show="*" if nome == "senha" else "").grid(
                row=i // 2, column=(i % 2) * 2 + 1, padx=(0, 14), pady=3, sticky="ew"
            )
        ttk.Label(form, text="Perfil").grid(row=0, column=4, padx=(0, 6), sticky="w")
        self.perfil_combo = ttk.Combobox(form, textvariable=self.vars["perfil"], state="readonly", width=20)
        self.perfil_combo.grid(row=0, column=5, sticky="w")
        ttk.Checkbutton(form, text="Ativo", variable=self.ativo).grid(row=1, column=5, sticky="w")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        acoes = ttk.Frame(self, style="Surface.TFrame")
        acoes.pack(fill="x", pady=(0, 8))
        ttk.Button(acoes, text="Novo", command=self.limpar).pack(side="left", padx=(0, 6))
        aplicar_permissao(ttk.Button(acoes, text="Criar usuario", command=self.criar, style="Primary.TButton"), "usuarios", "criar").pack(side="left", padx=(0, 6))
        aplicar_permissao(ttk.Button(acoes, text="Salvar alteracoes", command=self.atualizar), "usuarios", "editar").pack(side="left", padx=(0, 6))
        aplicar_permissao(ttk.Button(acoes, text="Redefinir senha", command=self.redefinir_senha), "usuarios", "editar").pack(side="left", padx=(0, 6))
        aplicar_permissao(ttk.Button(acoes, text="Desbloquear", command=self.desbloquear), "usuarios", "editar").pack(side="left")

        self.tree = _tabela(self, ["id", "nome", "login", "email", "perfil", "ativo", "bloqueado_ate"])
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)
        self.carregar()

    def carregar(self) -> None:
        try:
            perfis = self.controller.listar_perfis()
            usuarios = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.perfis = {p.nome: p.id for p in perfis if p.ativo}
        self.perfil_combo["values"] = list(self.perfis)
        for linha in self.tree.get_children():
            self.tree.delete(linha)
        for u in usuarios:
            self.tree.insert(
                "", "end", iid=str(u.id),
                values=[format_value(x) for x in (u.id, u.nome, u.login, u.email, u.perfil.nome, "sim" if u.ativo else "nao", u.bloqueado_ate)],
            )

    def limpar(self) -> None:
        for v in self.vars.values():
            v.set("")
        self.ativo.set(True)
        self.selecionado = None
        self.tree.selection_remove(self.tree.selection())

    def _selecionar(self, _evento) -> None:
        selecao = self.tree.selection()
        if not selecao:
            return
        self.selecionado = int(selecao[0])
        valores = self.tree.item(selecao[0], "values")
        self.vars["nome"].set(valores[1])
        self.vars["login"].set(valores[2])
        self.vars["email"].set(valores[3])
        self.vars["perfil"].set(valores[4])
        self.vars["senha"].set("")
        self.ativo.set(valores[5] == "sim")

    def _perfil_id(self) -> int:
        nome = self.vars["perfil"].get()
        if nome not in self.perfis:
            raise ValueError("Selecione o perfil.")
        return self.perfis[nome]

    def _exigir_selecao(self) -> int:
        if self.selecionado is None:
            raise ValueError("Selecione um usuario na tabela.")
        return self.selecionado

    def criar(self) -> None:
        v = self.vars
        if executar(
            lambda: self.controller.criar(v["nome"].get(), v["email"].get(), v["login"].get(), v["senha"].get(), self._perfil_id()),
            "Usuario criado. Ele precisara trocar a senha no primeiro acesso.", "Usuarios", self.carregar,
        ):
            self.limpar()

    def atualizar(self) -> None:
        v = self.vars
        executar(
            lambda: self.controller.atualizar(self._exigir_selecao(), v["nome"].get(), v["email"].get(), self._perfil_id(), self.ativo.get()),
            "Usuario atualizado.", "Usuarios", self.carregar,
        )

    def redefinir_senha(self) -> None:
        try:
            usuario_id = self._exigir_selecao()
        except ValueError as exc:
            messagebox.showwarning("Usuarios", str(exc))
            return
        nova = simpledialog.askstring("Redefinir senha", "Nova senha temporaria (min. 8, letras e numeros):", show="*", parent=self)
        if nova:
            executar(lambda: self.controller.redefinir_senha(usuario_id, nova), "Senha redefinida. O usuario devera troca-la no proximo login.", "Usuarios", self.carregar)

    def desbloquear(self) -> None:
        executar(lambda: self.controller.desbloquear(self._exigir_selecao()), "Conta desbloqueada.", "Usuarios", self.carregar)


class PermissoesFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.controller = PermissaoController()
        self.perfis: dict[str, int] = {}
        self.checks: dict[tuple[str, str], tk.BooleanVar] = {}
        self.perfil_var = tk.StringVar()
        _cabecalho(self, "Perfis e permissoes", "Defina o que cada perfil pode ver, criar, editar e excluir/cancelar em cada modulo.")

        topo = ttk.Frame(self, style="Surface.TFrame")
        topo.pack(fill="x", pady=(0, 8))
        ttk.Label(topo, text="Perfil").pack(side="left", padx=(0, 6))
        self.combo = ttk.Combobox(topo, textvariable=self.perfil_var, state="readonly", width=28)
        self.combo.pack(side="left", padx=(0, 10))
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.carregar_matriz())
        aplicar_permissao(ttk.Button(topo, text="Novo perfil", command=self.novo_perfil), "permissoes", "criar").pack(side="left", padx=(0, 6))
        self.botao_salvar = aplicar_permissao(ttk.Button(topo, text="Salvar permissoes", command=self.salvar, style="Primary.TButton"), "permissoes", "editar")
        self.botao_salvar.pack(side="left")

        grade = ttk.LabelFrame(self, text="Matriz de acesso", padding=12, style="Section.TLabelframe")
        grade.pack(fill="x")
        ttk.Label(grade, text="Modulo", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 30))
        for col, acao in enumerate(ACOES, start=1):
            ttk.Label(grade, text=acao.title(), font=("Segoe UI", 10, "bold")).grid(row=0, column=col, padx=12)
        self.widgets: list[ttk.Checkbutton] = []
        for linha, (modulo, rotulo) in enumerate(MODULOS.items(), start=1):
            ttk.Label(grade, text=rotulo).grid(row=linha, column=0, sticky="w", pady=1)
            for col, acao in enumerate(ACOES, start=1):
                var = tk.BooleanVar()
                self.checks[(modulo, acao)] = var
                check = ttk.Checkbutton(grade, variable=var)
                check.grid(row=linha, column=col)
                self.widgets.append(check)
        self.carregar()

    def carregar(self) -> None:
        try:
            perfis = self.controller.listar_perfis()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.perfis = {p.nome: p.id for p in perfis}
        self.combo["values"] = list(self.perfis)
        if self.perfis and not self.perfil_var.get():
            self.perfil_var.set(next(iter(self.perfis)))
        self.carregar_matriz()

    def carregar_matriz(self) -> None:
        nome = self.perfil_var.get()
        if nome not in self.perfis:
            return
        try:
            matriz = self.controller.carregar(self.perfis[nome])
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        for (modulo, acao), var in self.checks.items():
            var.set(acao in matriz.get(modulo, set()))
        somente_leitura = nome == PERFIL_ADMIN
        for check in self.widgets:
            check.state(["disabled"] if somente_leitura else ["!disabled"])
        self.botao_salvar.state(["disabled"] if somente_leitura else ["!disabled"])

    def novo_perfil(self) -> None:
        nome = simpledialog.askstring("Novo perfil", "Nome do perfil:", parent=self)
        if nome:
            if executar(lambda: self.controller.criar_perfil(nome), f"Perfil '{nome}' criado. Marque as permissoes e salve.", "Permissoes"):
                self.perfil_var.set(nome.strip())
                self.carregar()

    def salvar(self) -> None:
        nome = self.perfil_var.get()
        if nome not in self.perfis:
            return
        matriz = {m: {a for a in ACOES if self.checks[(m, a)].get()} for m in MODULOS}
        executar(lambda: self.controller.salvar_matriz(self.perfis[nome], matriz), "Permissoes salvas. Valem a partir do proximo login dos usuarios deste perfil.", "Permissoes")


class ConfiguracoesFrame(ttk.Frame):
    CHAVES_SUGERIDAS = ["empresa.nome", "empresa.cnpj", "empresa.telefone", "empresa.endereco", "empresa.cidade"]

    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.controller = SegurancaController()
        self.chave = tk.StringVar()
        self.valor = tk.StringVar()
        _cabecalho(self, "Configuracoes", "Parametros do sistema. 'empresa.nome' aparece no cabecalho da impressao da OS.")

        form = ttk.LabelFrame(self, text="Parametro", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="Chave").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Combobox(form, textvariable=self.chave, values=self.CHAVES_SUGERIDAS, width=28).grid(row=0, column=1, padx=(0, 12))
        ttk.Label(form, text="Valor").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.valor, width=50).grid(row=0, column=3, padx=(0, 12), sticky="ew")
        aplicar_permissao(ttk.Button(form, text="Salvar", command=self.salvar, style="Primary.TButton"), "configuracoes", "editar").grid(row=0, column=4)
        form.columnconfigure(3, weight=1)

        self.tree = _tabela(self, ["id", "chave", "valor"])
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)
        self.carregar()

    def carregar(self) -> None:
        for linha in self.tree.get_children():
            self.tree.delete(linha)
        try:
            itens = self.controller.listar_configuracoes()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        for item in itens:
            self.tree.insert("", "end", iid=str(item.id), values=[format_value(item.id), format_value(item.chave), format_value(item.valor)])

    def salvar(self) -> None:
        executar(lambda: self.controller.salvar_configuracao(self.chave.get(), self.valor.get()), "Parametro salvo.", "Configuracoes", self.carregar)

    def _selecionar(self, _evento) -> None:
        selecao = self.tree.selection()
        if selecao:
            valores = self.tree.item(selecao[0], "values")
            self.chave.set(valores[1])
            self.valor.set(valores[2])
