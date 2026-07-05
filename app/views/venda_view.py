import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.venda_controller import VendaController
from app.views.theme import format_value


class VendaFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
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

        ttk.Label(self, text="Vendas", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self, text="Crie orcamentos, adicione itens e finalize vendas com baixa de estoque e financeiro a receber.", style="Subtle.TLabel").pack(anchor="w", pady=(4, 14))
        self._criar_form_venda()
        self._criar_form_item()
        table_frame = ttk.LabelFrame(self, text="Orcamentos e vendas", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=["id", "cliente_id", "numero", "data_venda", "status", "valor_total"], show="headings", height=12)
        for column in ["id", "cliente_id", "numero", "data_venda", "status", "valor_total"]:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=140, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)
        self.carregar()

    def _criar_form_venda(self) -> None:
        form = ttk.LabelFrame(self, text="Orcamento / venda", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        fields = [("cliente_id", "Cliente ID"), ("numero", "Numero"), ("data_venda", "Data/hora ISO"), ("status", "Status")]
        for index, (name, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.venda_inputs[name], width=18).grid(row=0, column=index * 2 + 1, padx=(0, 12))
            form.columnconfigure(index * 2 + 1, weight=1)
        ttk.Button(form, text="Criar", command=self.criar_venda, style="Primary.TButton").grid(row=0, column=8)

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens e finalizacao", padding=14, style="Section.TLabelframe")
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
            form.columnconfigure(index * 2 + 1, weight=1)
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
            self.tree.insert("", "end", iid=str(item.id), values=[format_value(item.id), format_value(item.cliente_id), format_value(item.numero), format_value(item.data_venda), format_value(item.status), format_value(item.valor_total)])

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["venda_id"].set(selection[0])
