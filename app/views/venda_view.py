import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.lookup_controller import LookupController
from app.controllers.venda_controller import VendaController
from app.views.helpers import FORMAS_PAGAMENTO, ItensPanel, aplicar_permissao, executar, pedir_motivo
from app.views.widgets import IdVar, Seletor, TabelaFiltravel


class VendaFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = VendaController()
        lookups = LookupController()
        self.venda_inputs = {
            "cliente_id": IdVar(),
            "numero": tk.StringVar(),
            "data_venda": tk.StringVar(),
            "status": tk.StringVar(value="ORCAMENTO"),
        }
        self.item_inputs = {
            "venda_id": tk.StringVar(),
            "produto_id": IdVar(),
            "quantidade": tk.StringVar(value="1"),
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
        self._criar_form_venda(lookups)
        self._criar_form_item(lookups)
        self._criar_form_finalizacao()
        self.itens_panel = ItensPanel(
            self,
            ["id", "produto.descricao", "quantidade", "valor_unitario", "valor_total"],
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
        self.tabela = TabelaFiltravel(
            table_frame,
            ["id", "numero", "cliente", "data_venda", "status", "parcelas", "forma_pagamento", "valor_total"],
            altura=7,
            larguras={"id": 50, "numero": 100, "cliente": 190},
        )
        self.tabela.pack(fill="both", expand=True)
        self.tabela.ao_selecionar(self._selecionar)
        self.carregar()

    def _criar_form_venda(self, lookups) -> None:
        form = ttk.LabelFrame(self, text="Orcamento / venda", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Cliente").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.cliente_sel = Seletor(form, self.venda_inputs["cliente_id"], lookups.clientes, largura=30)
        self.cliente_sel.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        for index, (name, label) in enumerate([("numero", "Numero (auto)"), ("data_venda", "Data/hora ISO"), ("status", "Status")], start=1):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.venda_inputs[name], width=16).grid(row=0, column=index * 2 + 1, padx=(0, 10))
        form.columnconfigure(1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Criar", command=self.criar_venda, style="Primary.TButton"), "vendas", "criar").grid(row=0, column=8)

    def _criar_form_item(self, lookups) -> None:
        form = ttk.LabelFrame(self, text="Itens (selecione uma venda na tabela)", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Venda").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.item_inputs["venda_id"], width=8, state="readonly").grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Produto").grid(row=0, column=2, padx=(0, 6), sticky="w")
        self.produto_sel = Seletor(form, self.item_inputs["produto_id"], lookups.produtos, largura=34, ao_escolher=self._produto_escolhido)
        self.produto_sel.grid(row=0, column=3, padx=(0, 10), sticky="ew")
        for index, (name, label) in enumerate([("quantidade", "Qtd"), ("valor_unitario", "Valor unitario")], start=2):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.item_inputs[name], width=12).grid(row=0, column=index * 2 + 1, padx=(0, 10))
        form.columnconfigure(3, weight=1)
        aplicar_permissao(ttk.Button(form, text="Adicionar item", command=self.adicionar_item), "vendas", "criar").grid(row=0, column=8)

    def _produto_escolhido(self, opcao) -> None:
        if opcao and opcao[2]:
            self.item_inputs["valor_unitario"].set(opcao[2])  # sugere o preco de venda cadastrado

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
        valor = self.item_inputs["venda_id"].get()
        if not valor:
            raise ValueError("Selecione uma venda na tabela.")
        return int(valor)

    def criar_venda(self) -> None:
        executar(
            lambda: self.controller.criar_venda({n: v.get() for n, v in self.venda_inputs.items()}, usuario_id=self.usuario.id),
            "Venda/orcamento criado.", "Vendas", self.carregar,
        )

    def adicionar_item(self) -> None:
        executar(
            lambda: self.controller.adicionar_item({"venda_id": self._venda_id(), **{n: v.get() for n, v in self.item_inputs.items() if n != "venda_id"}}),
            "Item adicionado.", "Vendas", lambda: (self.carregar(), self.itens_panel.mostrar(self.item_inputs["venda_id"].get())),
        )

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
        try:
            vendas = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.tabela.preencher(
            [
                (v.id, [v.id, v.numero, v.cliente.nome if v.cliente else "", v.data_venda, v.status, v.parcelas, v.forma_pagamento, v.valor_total])
                for v in vendas
            ]
        )
        self.cliente_sel.recarregar()
        self.produto_sel.recarregar()

    def _selecionar(self, _event) -> None:
        selection = self.tabela.selection()
        if selection:
            self.item_inputs["venda_id"].set(selection[0])
            self.itens_panel.mostrar(selection[0])
