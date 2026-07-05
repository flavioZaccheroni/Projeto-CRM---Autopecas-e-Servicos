import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.compra_controller import CompraController


class CompraFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=16)
        self.usuario = usuario
        self.controller = CompraController()
        self.compra_inputs = {
            "fornecedor_id": tk.StringVar(),
            "numero": tk.StringVar(),
            "data_compra": tk.StringVar(),
            "status": tk.StringVar(value="ABERTA"),
        }
        self.item_inputs = {
            "compra_id": tk.StringVar(),
            "produto_id": tk.StringVar(),
            "quantidade": tk.StringVar(),
            "valor_unitario": tk.StringVar(),
        }

        ttk.Label(self, text="Compras", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 12))
        self._criar_form_compra()
        self._criar_form_item()
        self.tree = ttk.Treeview(self, columns=["id", "fornecedor_id", "numero", "data_compra", "status", "valor_total"], show="headings", height=12)
        for column in ["id", "fornecedor_id", "numero", "data_compra", "status", "valor_total"]:
            self.tree.heading(column, text=column.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)
        self.carregar()

    def _criar_form_compra(self) -> None:
        form = ttk.LabelFrame(self, text="Pedido de compra", padding=10)
        form.pack(fill="x", pady=(0, 8))
        for index, (name, label) in enumerate([("fornecedor_id", "Fornecedor ID"), ("numero", "Numero"), ("data_compra", "Data AAAA-MM-DD"), ("status", "Status")]):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.compra_inputs[name], width=18).grid(row=0, column=index * 2 + 1, padx=(0, 12))
        ttk.Button(form, text="Criar compra", command=self.criar_compra).grid(row=0, column=8)

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens e recebimento", padding=10)
        form.pack(fill="x", pady=(0, 12))
        for index, (name, label) in enumerate([("compra_id", "Compra ID"), ("produto_id", "Produto ID"), ("quantidade", "Quantidade"), ("valor_unitario", "Valor unitario")]):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.item_inputs[name], width=16).grid(row=0, column=index * 2 + 1, padx=(0, 12))
        ttk.Button(form, text="Adicionar item", command=self.adicionar_item).grid(row=0, column=8, padx=(0, 8))
        ttk.Button(form, text="Receber compra", command=self.receber_compra).grid(row=0, column=9)

    def criar_compra(self) -> None:
        try:
            self.controller.criar_compra(
                {name: var.get() for name, var in self.compra_inputs.items()},
                usuario_id=self.usuario.id,
            )
            self.carregar()
            messagebox.showinfo("Compras", "Compra criada.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def adicionar_item(self) -> None:
        try:
            self.controller.adicionar_item({name: var.get() for name, var in self.item_inputs.items()})
            self.carregar()
            messagebox.showinfo("Compras", "Item adicionado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def receber_compra(self) -> None:
        try:
            self.controller.receber_compra(int(self.item_inputs["compra_id"].get()), usuario_id=self.usuario.id)
            self.carregar()
            messagebox.showinfo("Compras", "Compra recebida e estoque atualizado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.controller.listar():
            self.tree.insert("", "end", iid=str(item.id), values=[item.id, item.fornecedor_id, item.numero, item.data_compra, item.status, item.valor_total])

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["compra_id"].set(selection[0])
