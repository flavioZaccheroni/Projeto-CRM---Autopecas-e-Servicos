import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.estoque_controller import EstoqueController


class EstoqueFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=16)
        self.usuario = usuario
        self.controller = EstoqueController()
        self.inputs = {
            "produto_id": tk.StringVar(),
            "tipo": tk.StringVar(value="ENTRADA"),
            "quantidade": tk.StringVar(),
            "origem": tk.StringVar(value="MANUAL"),
            "localizacao": tk.StringVar(),
        }

        ttk.Label(self, text="Estoque", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 12))
        form = ttk.Frame(self)
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

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=12)
        ttk.Button(actions, text="Registrar movimento", command=self.movimentar).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Atualizar", command=self.carregar).pack(side="left")

        ttk.Label(self, text="Saldo atual").pack(anchor="w")
        self.estoque_tree = ttk.Treeview(self, columns=["id", "produto_id", "quantidade_atual", "localizacao"], show="headings", height=7)
        for column in ["id", "produto_id", "quantidade_atual", "localizacao"]:
            self.estoque_tree.heading(column, text=column.replace("_", " ").title())
        self.estoque_tree.pack(fill="x", pady=(0, 12))

        ttk.Label(self, text="Movimentacoes").pack(anchor="w")
        self.mov_tree = ttk.Treeview(self, columns=["id", "produto_id", "tipo", "origem", "quantidade", "saldo_anterior", "saldo_posterior"], show="headings", height=8)
        for column in ["id", "produto_id", "tipo", "origem", "quantidade", "saldo_anterior", "saldo_posterior"]:
            self.mov_tree.heading(column, text=column.replace("_", " ").title())
        self.mov_tree.pack(fill="both", expand=True)
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
            self.estoque_tree.insert("", "end", values=[item.id, item.produto_id, item.quantidade_atual, item.localizacao])
        for item in self.controller.listar_movimentacoes():
            self.mov_tree.insert("", "end", values=[item.id, item.produto_id, item.tipo, item.origem, item.quantidade, item.saldo_anterior, item.saldo_posterior])
