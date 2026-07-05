import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.estoque_controller import EstoqueController
from app.views.theme import format_value


class EstoqueFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = EstoqueController()
        self.inputs = {
            "produto_id": tk.StringVar(),
            "tipo": tk.StringVar(value="ENTRADA"),
            "quantidade": tk.StringVar(),
            "origem": tk.StringVar(value="MANUAL"),
            "localizacao": tk.StringVar(),
        }

        ttk.Label(self, text="Estoque", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self, text="Controle saldo, entradas, saidas e ajustes com historico de movimentacao.", style="Subtle.TLabel").pack(anchor="w", pady=(4, 14))
        form = ttk.LabelFrame(self, text="Movimento de estoque", padding=14, style="Section.TLabelframe")
        form.pack(fill="x")
        labels = [
            ("produto_id", "Produto ID"),
            ("tipo", "Tipo"),
            ("quantidade", "Quantidade"),
            ("origem", "Origem"),
            ("localizacao", "Localizacao"),
        ]
        for index, (name, label) in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, sticky="w", padx=(0, 6))
            if name == "tipo":
                widget = ttk.Combobox(form, textvariable=self.inputs[name], values=["ENTRADA", "SAIDA", "AJUSTE"], width=12)
            else:
                widget = ttk.Entry(form, textvariable=self.inputs[name], width=18)
            widget.grid(row=0, column=index * 2 + 1, padx=(0, 12))
            form.columnconfigure(index * 2 + 1, weight=1)

        actions = ttk.Frame(self, style="Surface.TFrame")
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Registrar movimento", command=self.movimentar, style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Atualizar", command=self.carregar).pack(side="left")

        saldo_frame = ttk.LabelFrame(self, text="Saldo atual", padding=10, style="Section.TLabelframe")
        saldo_frame.pack(fill="x", pady=(0, 12))
        self.estoque_tree = ttk.Treeview(saldo_frame, columns=["id", "produto_id", "quantidade_atual", "localizacao"], show="headings", height=7)
        for column in ["id", "produto_id", "quantidade_atual", "localizacao"]:
            self.estoque_tree.heading(column, text=column.replace("_", " ").title())
            self.estoque_tree.column(column, width=140, anchor="w")
        self.estoque_tree.pack(fill="x")

        mov_frame = ttk.LabelFrame(self, text="Movimentacoes", padding=10, style="Section.TLabelframe")
        mov_frame.pack(fill="both", expand=True)
        self.mov_tree = ttk.Treeview(mov_frame, columns=["id", "produto_id", "tipo", "origem", "quantidade", "saldo_anterior", "saldo_posterior"], show="headings", height=8)
        for column in ["id", "produto_id", "tipo", "origem", "quantidade", "saldo_anterior", "saldo_posterior"]:
            self.mov_tree.heading(column, text=column.replace("_", " ").title())
            self.mov_tree.column(column, width=130, anchor="w")
        yscroll = ttk.Scrollbar(mov_frame, orient="vertical", command=self.mov_tree.yview)
        self.mov_tree.configure(yscrollcommand=yscroll.set)
        self.mov_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        mov_frame.columnconfigure(0, weight=1)
        mov_frame.rowconfigure(0, weight=1)
        self.carregar()

    def movimentar(self) -> None:
        try:
            self.controller.movimentar(
                {name: var.get() for name, var in self.inputs.items()},
                usuario_id=self.usuario.id,
            )
            self.carregar()
            messagebox.showinfo("Estoque", "Movimento registrado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for tree in [self.estoque_tree, self.mov_tree]:
            for row in tree.get_children():
                tree.delete(row)
        for item in self.controller.listar():
            self.estoque_tree.insert("", "end", values=[format_value(item.id), format_value(item.produto_id), format_value(item.quantidade_atual), format_value(item.localizacao)])
        for item in self.controller.listar_movimentacoes():
            self.mov_tree.insert("", "end", values=[format_value(item.id), format_value(item.produto_id), format_value(item.tipo), format_value(item.origem), format_value(item.quantidade), format_value(item.saldo_anterior), format_value(item.saldo_posterior)])
