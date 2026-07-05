import tkinter as tk
from tkinter import messagebox, ttk


class CrudFrame(ttk.Frame):
    def __init__(self, master, title: str, controller, fields: list[dict], columns: list[str]) -> None:
        super().__init__(master, padding=16)
        self.controller = controller
        self.fields = fields
        self.columns = columns
        self.inputs: dict[str, tk.Variable] = {}

        ttk.Label(self, text=title, font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 12))

        form = ttk.Frame(self)
        form.pack(fill="x")
        for index, field in enumerate(fields):
            row = index // 3
            col = (index % 3) * 2
            ttk.Label(form, text=field["label"]).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=4)
            variable = tk.BooleanVar(value=True) if field.get("type") == "bool" else tk.StringVar()
            self.inputs[field["name"]] = variable
            if field.get("type") == "bool":
                widget = ttk.Checkbutton(form, variable=variable)
            else:
                widget = ttk.Entry(form, textvariable=variable, width=24)
            widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=4)

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Novo", command=self.limpar).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Salvar", command=self.salvar).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Atualizar", command=self.carregar).pack(side="left")

        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        for column in columns:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=120, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)

        self.itens: dict[str, object] = {}
        self.carregar()

    def carregar(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.itens.clear()
        for item in self.controller.listar():
            values = [getattr(item, column, "") for column in self.columns]
            item_id = str(getattr(item, "id"))
            self.itens[item_id] = item
            self.tree.insert("", "end", iid=item_id, values=values)

    def limpar(self) -> None:
        for field in self.fields:
            variable = self.inputs[field["name"]]
            if field.get("type") == "bool":
                variable.set(True)
            else:
                variable.set("")
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
        if not selection:
            return
        item = self.itens[selection[0]]
        for field in self.fields:
            name = field["name"]
            value = getattr(item, name, "")
            self.inputs[name].set(value if value is not None else "")
