import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.lookup_controller import LookupController
from app.utils.sessao import Sessao
from app.views.widgets import IdVar, Seletor, TabelaFiltravel, valor_coluna


class CrudFrame(ttk.Frame):
    """Tela generica de cadastro: formulario + tabela com busca.

    Cada campo de `fields` pode ter: `type: bool`, `lookup: <nome do seletor>` (ID com busca),
    `choices: [...]` (lista) e `readonly: True` (so aceita os valores da lista).
    """

    def __init__(self, master, title: str, controller, fields: list[dict], columns: list[str]) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.controller = controller
        self.fields = fields
        self.columns = columns
        self.inputs: dict[str, tk.Variable] = {}
        self.seletores: dict[str, Seletor] = {}
        lookups = LookupController()

        header = ttk.Frame(self, style="Surface.TFrame")
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text=title, style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Cadastre, edite e consulte registros deste modulo. Ctrl+F busca na tabela.", style="Subtle.TLabel").pack(anchor="w", pady=(4, 0))

        form = ttk.LabelFrame(self, text="Dados do registro", padding=14, style="Section.TLabelframe")
        form.pack(fill="x")
        for index, field in enumerate(fields):
            row = index // 3
            col = (index % 3) * 2
            ttk.Label(form, text=field["label"]).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
            nome = field["name"]
            if field.get("type") == "bool":
                variable: tk.Variable = tk.BooleanVar(value=True)
                widget = ttk.Checkbutton(form, variable=variable)
            elif field.get("lookup"):
                variable = IdVar()
                widget = Seletor(form, variable, getattr(lookups, field["lookup"]), largura=24)
                self.seletores[nome] = widget
            elif field.get("choices"):
                variable = tk.StringVar()
                widget = ttk.Combobox(form, textvariable=variable, values=field["choices"], width=22, state="readonly" if field.get("readonly") else "normal")
            else:
                variable = tk.StringVar()
                widget = ttk.Entry(form, textvariable=variable, width=24)
            self.inputs[nome] = variable
            widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=4)
            form.columnconfigure(col + 1, weight=1)

        actions = ttk.Frame(self, style="Surface.TFrame")
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Novo", command=self.limpar).pack(side="left", padx=(0, 8))
        modulo = getattr(controller, "modulo", "")
        self.botao_salvar = ttk.Button(actions, text="Salvar", command=self.salvar, style="Primary.TButton")
        self.botao_salvar.pack(side="left", padx=(0, 8))
        if modulo and not (Sessao.pode(modulo, "criar") or Sessao.pode(modulo, "editar")):
            self.botao_salvar.state(["disabled"])
        ttk.Button(actions, text="Atualizar", command=self.carregar).pack(side="left")

        table_frame = ttk.LabelFrame(self, text="Registros", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        self.tabela = TabelaFiltravel(table_frame, columns, altura=12)
        self.tabela.pack(fill="both", expand=True)
        self.tree = self.tabela.tree
        self.tabela.ao_selecionar(self._selecionar)

        self.itens: dict[str, object] = {}
        self.carregar()

    def carregar(self) -> None:
        self.itens.clear()
        try:
            registros = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        linhas = []
        for item in registros:
            item_id = str(getattr(item, "id"))
            self.itens[item_id] = item
            linhas.append((item_id, [valor_coluna(item, coluna) for coluna in self.columns]))
        self.tabela.preencher(linhas)
        for seletor in self.seletores.values():
            seletor.recarregar()

    def limpar(self) -> None:
        for field in self.fields:
            variable = self.inputs[field["name"]]
            variable.set(True if field.get("type") == "bool" else "")
        self.tree.selection_remove(self.tree.selection())

    def salvar(self) -> None:
        try:
            dados = {name: variable.get() for name, variable in self.inputs.items()}
            selection = self.tree.selection()
            if selection:
                dados["id"] = selection[0]
            self.controller.salvar(dados)
            self.limpar()
            self.carregar()
            messagebox.showinfo("Salvar", "Registro salvo com sucesso.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if not selection or selection[0] not in self.itens:
            return
        item = self.itens[selection[0]]
        for field in self.fields:
            name = field["name"]
            value = getattr(item, name, "")
            if name in self.seletores:
                self.seletores[name].definir_id(value)
            else:
                self.inputs[name].set(value if value is not None else "")
