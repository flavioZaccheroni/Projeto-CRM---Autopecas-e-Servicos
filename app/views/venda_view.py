import tkinter as tk
from tkinter import ttk

from app.controllers.venda_controller import VendaController
from app.views.helpers import FORMAS_PAGAMENTO, ItensPanel, aplicar_permissao, executar, pedir_motivo
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
        }
        self.fin_inputs = {
            "data_vencimento": tk.StringVar(),
            "parcelas": tk.StringVar(value="1"),
            "forma_pagamento": tk.StringVar(),
        }

        ttk.Label(self, text="Vendas", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Orcamento -> aprovacao -> venda, com baixa de estoque, parcelamento e contas a receber. Numero em branco = automatico.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 10))
        self._criar_form_venda()
        self._criar_form_item()
        self._criar_form_finalizacao()
        self.itens_panel = ItensPanel(
            self,
            ["id", "produto_id", "quantidade", "valor_unitario", "valor_total"],
            self.controller.listar_itens,
            self.controller.atualizar_item,
            self.controller.remover_item,
            lambda: (self.item_inputs["quantidade"].get(), self.item_inputs["valor_unitario"].get()),
            "vendas",
            self.carregar,
        )
        self.itens_panel.pack(fill="x", pady=(0, 8))

        table_frame = ttk.LabelFrame(self, text="Orcamentos e vendas", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        colunas = ["id", "cliente_id", "numero", "data_venda", "status", "parcelas", "forma_pagamento", "valor_total"]
        self.tree = ttk.Treeview(table_frame, columns=colunas, show="headings", height=8)
        for column in colunas:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=120, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)
        self.carregar()

    def _criar_form_venda(self) -> None:
        form = ttk.LabelFrame(self, text="Orcamento / venda", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        fields = [("cliente_id", "Cliente ID"), ("numero", "Numero (auto)"), ("data_venda", "Data/hora ISO"), ("status", "Status")]
        for index, (name, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.venda_inputs[name], width=16).grid(row=0, column=index * 2 + 1, padx=(0, 10))
            form.columnconfigure(index * 2 + 1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Criar", command=self.criar_venda, style="Primary.TButton"), "vendas", "criar").grid(row=0, column=8)

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        fields = [("venda_id", "Venda ID"), ("produto_id", "Produto ID"), ("quantidade", "Quantidade"), ("valor_unitario", "Valor unitario")]
        for index, (name, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.item_inputs[name], width=14).grid(row=0, column=index * 2 + 1, padx=(0, 10))
            form.columnconfigure(index * 2 + 1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Adicionar item", command=self.adicionar_item), "vendas", "criar").grid(row=0, column=8)

    def _criar_form_finalizacao(self) -> None:
        form = ttk.LabelFrame(self, text="Aprovacao, finalizacao e cancelamento", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="1o vencimento").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.fin_inputs["data_vencimento"], width=12).grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Parcelas").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Spinbox(form, from_=1, to=60, textvariable=self.fin_inputs["parcelas"], width=5).grid(row=0, column=3, padx=(0, 10))
        ttk.Label(form, text="Pagamento").grid(row=0, column=4, padx=(0, 6), sticky="w")
        ttk.Combobox(form, textvariable=self.fin_inputs["forma_pagamento"], values=FORMAS_PAGAMENTO, width=16).grid(row=0, column=5, padx=(0, 12))
        aplicar_permissao(ttk.Button(form, text="Aprovar orcamento", command=self.aprovar), "vendas", "editar").grid(row=0, column=6, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Recusar", command=self.recusar), "vendas", "editar").grid(row=0, column=7, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Finalizar venda", command=self.finalizar_venda, style="Primary.TButton"), "vendas", "editar").grid(row=0, column=8, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Cancelar", command=self.cancelar), "vendas", "excluir").grid(row=0, column=9)

    def _venda_id(self) -> int:
        return int(self.item_inputs["venda_id"].get())

    def criar_venda(self) -> None:
        executar(
            lambda: self.controller.criar_venda({n: v.get() for n, v in self.venda_inputs.items()}, usuario_id=self.usuario.id),
            "Venda/orcamento criado.", "Vendas", self.carregar,
        )

    def adicionar_item(self) -> None:
        def acao():
            self.controller.adicionar_item({**{n: v.get() for n, v in self.item_inputs.items()}})

        executar(acao, "Item adicionado.", "Vendas", lambda: (self.carregar(), self.itens_panel.mostrar(self.item_inputs["venda_id"].get())))

    def aprovar(self) -> None:
        executar(lambda: self.controller.aprovar_orcamento(self._venda_id()), "Orcamento aprovado.", "Vendas", self.carregar)

    def recusar(self) -> None:
        motivo = pedir_motivo(self, "Recusar orcamento", "Motivo da recusa:")
        if motivo:
            executar(lambda: self.controller.recusar_orcamento(self._venda_id(), motivo), "Orcamento recusado.", "Vendas", self.carregar)

    def finalizar_venda(self) -> None:
        executar(
            lambda: self.controller.finalizar_venda(
                self._venda_id(),
                usuario_id=self.usuario.id,
                data_vencimento=self.fin_inputs["data_vencimento"].get(),
                parcelas=self.fin_inputs["parcelas"].get(),
                forma_pagamento=self.fin_inputs["forma_pagamento"].get(),
            ),
            "Venda finalizada, estoque baixado e financeiro gerado.", "Vendas", self.carregar,
        )

    def cancelar(self) -> None:
        motivo = pedir_motivo(self, "Cancelar venda", "Motivo do cancelamento (estoque e financeiro serao estornados):")
        if motivo:
            executar(
                lambda: self.controller.cancelar_venda(self._venda_id(), motivo, usuario_id=self.usuario.id),
                "Venda cancelada.", "Vendas", self.carregar,
            )

    def carregar(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            vendas = self.controller.listar()
        except Exception as exc:
            from tkinter import messagebox

            messagebox.showerror("Erro", str(exc))
            return
        for v in vendas:
            self.tree.insert(
                "", "end", iid=str(v.id),
                values=[format_value(x) for x in (v.id, v.cliente_id, v.numero, v.data_venda, v.status, v.parcelas, v.forma_pagamento, v.valor_total)],
            )

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["venda_id"].set(selection[0])
            self.itens_panel.mostrar(selection[0])
