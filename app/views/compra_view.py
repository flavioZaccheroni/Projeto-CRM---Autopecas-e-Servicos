import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.compra_controller import CompraController
from app.controllers.lookup_controller import LookupController
from app.views.helpers import ItensPanel, aplicar_permissao, executar, pedir_motivo
from app.views.widgets import IdVar, Seletor, TabelaFiltravel


class CompraFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = CompraController()
        lookups = LookupController()
        self.compra_inputs = {
            "fornecedor_id": IdVar(),
            "numero": tk.StringVar(),
            "data_compra": tk.StringVar(),
            "status": tk.StringVar(value="ABERTA"),
        }
        self.item_inputs = {
            "compra_id": tk.StringVar(),
            "produto_id": IdVar(),
            "quantidade": tk.StringVar(value="1"),
            "valor_unitario": tk.StringVar(),
        }
        self.fin_inputs = {"data_vencimento": tk.StringVar(), "parcelas": tk.StringVar(value="1")}

        ttk.Label(self, text="Compras", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Receba mercadorias com entrada automatica em estoque e conta a pagar gerada. Numero em branco = automatico.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 10))
        self._criar_form_compra(lookups)
        self._criar_form_item(lookups)
        self._criar_form_recebimento()
        self.itens_panel = ItensPanel(
            self,
            ["id", "produto.descricao", "quantidade", "valor_unitario", "valor_total"],
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
        self.tabela = TabelaFiltravel(
            table_frame,
            ["id", "numero", "fornecedor", "data_compra", "status", "valor_total"],
            altura=7,
            larguras={"id": 50, "numero": 100, "fornecedor": 210},
        )
        self.tabela.pack(fill="both", expand=True)
        self.tabela.ao_selecionar(self._selecionar)
        self.carregar()

    def _criar_form_compra(self, lookups) -> None:
        form = ttk.LabelFrame(self, text="Pedido de compra", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Fornecedor").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.fornecedor_sel = Seletor(form, self.compra_inputs["fornecedor_id"], lookups.fornecedores, largura=30)
        self.fornecedor_sel.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        campos = [("numero", "Numero (auto)"), ("data_compra", "Data AAAA-MM-DD"), ("status", "Status")]
        for index, (name, label) in enumerate(campos, start=1):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.compra_inputs[name], width=16).grid(row=0, column=index * 2 + 1, padx=(0, 10))
        form.columnconfigure(1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Criar compra", command=self.criar_compra, style="Primary.TButton"), "compras", "criar").grid(row=0, column=8)

    def _criar_form_item(self, lookups) -> None:
        form = ttk.LabelFrame(self, text="Itens (selecione um pedido na tabela)", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Compra").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.item_inputs["compra_id"], width=8, state="readonly").grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Produto").grid(row=0, column=2, padx=(0, 6), sticky="w")
        self.produto_sel = Seletor(form, self.item_inputs["produto_id"], lookups.produtos, largura=34)
        self.produto_sel.grid(row=0, column=3, padx=(0, 10), sticky="ew")
        for index, (name, label) in enumerate([("quantidade", "Qtd"), ("valor_unitario", "Custo unitario")], start=2):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.item_inputs[name], width=12).grid(row=0, column=index * 2 + 1, padx=(0, 10))
        form.columnconfigure(3, weight=1)
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
        valor = self.item_inputs["compra_id"].get()
        if not valor:
            raise ValueError("Selecione um pedido na tabela.")
        return int(valor)

    def criar_compra(self) -> None:
        executar(
            lambda: self.controller.criar_compra({n: v.get() for n, v in self.compra_inputs.items()}, usuario_id=self.usuario.id),
            "Compra criada.", "Compras", self.carregar,
        )

    def adicionar_item(self) -> None:
        executar(
            lambda: self.controller.adicionar_item({"compra_id": self._compra_id(), **{n: v.get() for n, v in self.item_inputs.items() if n != "compra_id"}}),
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
        try:
            compras = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.tabela.preencher(
            [
                (c.id, [c.id, c.numero, c.fornecedor.razao_social if c.fornecedor else "", c.data_compra, c.status, c.valor_total])
                for c in compras
            ]
        )
        self.fornecedor_sel.recarregar()
        self.produto_sel.recarregar()

    def _selecionar(self, _event) -> None:
        selection = self.tabela.selection()
        if selection:
            self.item_inputs["compra_id"].set(selection[0])
            self.itens_panel.mostrar(selection[0])
