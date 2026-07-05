import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.venda_controller import VendaController


class VendaFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=16)
        self.usuario = usuario
        self.controller = VendaController()
        self.venda_inputs = {
            "cliente_id": tk.StringVar(),
            "numero": tk.StringVar(),
            "data_venda": tk.StringVar(),
            "status": tk.StringVar(value="ORCAMENTO"),
        }
        self.item_inputs = {
            "venda_id": tk.StringVar(),
            "produto_id": tk.StringVar(),
            "quantidade": tk.StringVar(),
            "valor_unitario": tk.StringVar(),
            "data_vencimento": tk.StringVar(),
        }

        ttk.Label(self, text="Vendas", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 12))
        self._criar_form_venda()
        self._criar_form_item()
        self.tree = ttk.Treeview(self, columns=["id", "cliente_id", "numero", "data_venda", "status", "valor_total"], show="headings", height=12)
        for column in ["id", "cliente_id", "numero", "data_venda", "status", "valor_total"]:
            self.tree.heading(column, text=column.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)
        self.carregar()

    def _criar_form_venda(self) -> None:
        form = ttk.LabelFrame(self, text="Orcamento / venda", padding=10)
        form.pack(fill="x", pady=(0, 8))
        fields = [("cliente_id", "Cliente ID"), ("numero", "Numero"), ("data_venda", "Data/hora ISO"), ("status", "Status")]
        for index, (name, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.venda_inputs[name], width=18).grid(row=0, column=index * 2 + 1, padx=(0, 12))
        ttk.Button(form, text="Criar", command=self.criar_venda).grid(row=0, column=8)

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens e finalizacao", padding=10)
        form.pack(fill="x", pady=(0, 12))
        fields = [
            ("venda_id", "Venda ID"),
            ("produto_id", "Produto ID"),
            ("quantidade", "Quantidade"),
            ("valor_unitario", "Valor unitario"),
            ("data_vencimento", "Vencimento"),
        ]
        for index, (name, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.item_inputs[name], width=14).grid(row=0, column=index * 2 + 1, padx=(0, 10))
        ttk.Button(form, text="Adicionar item", command=self.adicionar_item).grid(row=0, column=10, padx=(0, 8))
        ttk.Button(form, text="Finalizar", command=self.finalizar_venda).grid(row=0, column=11)

    def criar_venda(self) -> None:
        try:
            self.controller.criar_venda(
                {name: var.get() for name, var in self.venda_inputs.items()},
                usuario_id=self.usuario.id,
            )
            self.carregar()
            messagebox.showinfo("Vendas", "Venda/orcamento criado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def adicionar_item(self) -> None:
        try:
            self.controller.adicionar_item({name: var.get() for name, var in self.item_inputs.items()})
            self.carregar()
            messagebox.showinfo("Vendas", "Item adicionado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def finalizar_venda(self) -> None:
        try:
            self.controller.finalizar_venda(
                int(self.item_inputs["venda_id"].get()),
                usuario_id=self.usuario.id,
                data_vencimento=self.item_inputs["data_vencimento"].get(),
            )
            self.carregar()
            messagebox.showinfo("Vendas", "Venda finalizada, estoque baixado e financeiro gerado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.controller.listar():
            self.tree.insert("", "end", iid=str(item.id), values=[item.id, item.cliente_id, item.numero, item.data_venda, item.status, item.valor_total])

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["venda_id"].set(selection[0])
