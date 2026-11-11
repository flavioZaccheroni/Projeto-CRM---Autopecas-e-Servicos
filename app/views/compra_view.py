import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.compra_controller import CompraController
from app.views.helpers import ItensPanel, aplicar_permissao, executar, pedir_motivo
from app.views.theme import format_value


class CompraFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
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
        self.fin_inputs = {"data_vencimento": tk.StringVar(), "parcelas": tk.StringVar(value="1")}

        ttk.Label(self, text="Compras", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Receba mercadorias com entrada automatica em estoque e conta a pagar gerada. Numero em branco = automatico.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 10))
        self._criar_form_compra()
        self._criar_form_item()
        self._criar_form_recebimento()
        self.itens_panel = ItensPanel(
            self,
            ["id", "produto_id", "quantidade", "valor_unitario", "valor_total"],
            self.controller.listar_itens,
            self.controller.atualizar_item,
            self.controller.remover_item,
            lambda: (self.item_inputs["quantidade"].get(), self.item_inputs["valor_unitario"].get()),
            "compras",
            self.carregar,
        )
        self.itens_panel.pack(fill="x", pady=(0, 8))

        table_frame = ttk.LabelFrame(self, text="Pedidos", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        colunas = ["id", "fornecedor_id", "numero", "data_compra", "status", "valor_total"]
        self.tree = ttk.Treeview(table_frame, columns=colunas, show="headings", height=8)
        for column in colunas:
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

    def _criar_form_compra(self) -> None:
        form = ttk.LabelFrame(self, text="Pedido de compra", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        campos = [("fornecedor_id", "Fornecedor ID"), ("numero", "Numero (auto)"), ("data_compra", "Data AAAA-MM-DD"), ("status", "Status")]
        for index, (name, label) in enumerate(campos):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.compra_inputs[name], width=16).grid(row=0, column=index * 2 + 1, padx=(0, 10))
            form.columnconfigure(index * 2 + 1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Criar compra", command=self.criar_compra, style="Primary.TButton"), "compras", "criar").grid(row=0, column=8)

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        campos = [("compra_id", "Compra ID"), ("produto_id", "Produto ID"), ("quantidade", "Quantidade"), ("valor_unitario", "Valor unitario")]
        for index, (name, label) in enumerate(campos):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.item_inputs[name], width=14).grid(row=0, column=index * 2 + 1, padx=(0, 10))
            form.columnconfigure(index * 2 + 1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Adicionar item", command=self.adicionar_item), "compras", "criar").grid(row=0, column=8)

    def _criar_form_recebimento(self) -> None:
        form = ttk.LabelFrame(self, text="Recebimento (gera conta a pagar) e cancelamento", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="1o vencimento").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.fin_inputs["data_vencimento"], width=12).grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Parcelas").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Spinbox(form, from_=1, to=60, textvariable=self.fin_inputs["parcelas"], width=5).grid(row=0, column=3, padx=(0, 12))
        aplicar_permissao(ttk.Button(form, text="Receber compra", command=self.receber_compra, style="Primary.TButton"), "compras", "editar").grid(row=0, column=4, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Cancelar compra", command=self.cancelar), "compras", "excluir").grid(row=0, column=5)

    def _compra_id(self) -> int:
        return int(self.item_inputs["compra_id"].get())

    def criar_compra(self) -> None:
        executar(
            lambda: self.controller.criar_compra({n: v.get() for n, v in self.compra_inputs.items()}, usuario_id=self.usuario.id),
            "Compra criada.", "Compras", self.carregar,
        )

    def adicionar_item(self) -> None:
        executar(
            lambda: self.controller.adicionar_item({n: v.get() for n, v in self.item_inputs.items()}),
            "Item adicionado.", "Compras",
            lambda: (self.carregar(), self.itens_panel.mostrar(self.item_inputs["compra_id"].get())),
        )

    def receber_compra(self) -> None:
        executar(
            lambda: self.controller.receber_compra(
                self._compra_id(),
                usuario_id=self.usuario.id,
                data_vencimento=self.fin_inputs["data_vencimento"].get(),
                parcelas=self.fin_inputs["parcelas"].get(),
            ),
            "Compra recebida, estoque atualizado e conta a pagar gerada.", "Compras", self.carregar,
        )

    def cancelar(self) -> None:
        motivo = pedir_motivo(self, "Cancelar compra", "Motivo (se ja recebida, o estoque e o financeiro serao revertidos):")
        if motivo:
            executar(
                lambda: self.controller.cancelar_compra(self._compra_id(), motivo, usuario_id=self.usuario.id),
                "Compra cancelada.", "Compras", self.carregar,
            )

    def carregar(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            compras = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        for c in compras:
            self.tree.insert(
                "", "end", iid=str(c.id),
                values=[format_value(x) for x in (c.id, c.fornecedor_id, c.numero, c.data_compra, c.status, c.valor_total)],
            )

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["compra_id"].set(selection[0])
            self.itens_panel.mostrar(selection[0])
