import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.financeiro_controller import FinanceiroController
from app.controllers.lookup_controller import LookupController
from app.views.helpers import aplicar_permissao
from app.views.theme import format_value
from app.views.widgets import IdVar, Seletor, TabelaFiltravel


class FinanceiroFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = FinanceiroController()
        self.lookups = LookupController()
        self.inputs = {
            "tipo": tk.StringVar(value="RECEBER"),
            "descricao": tk.StringVar(),
            "valor": tk.StringVar(),
            "data_vencimento": tk.StringVar(),
            "cliente_id": IdVar(),
            "fornecedor_id": IdVar(),
        }
        self.baixa_inputs = {
            "lancamento_id": tk.StringVar(),
            "forma_pagamento": tk.StringVar(value="DINHEIRO"),
            "data_pagamento": tk.StringVar(),
        }

        ttk.Label(self, text="Financeiro", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Controle contas a pagar e receber, baixa de pagamentos, estornos e caixa. Selecione um lancamento na tabela para baixar.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 14))
        self._criar_resumo()
        self._criar_form_lancamento()
        self._criar_form_baixa()
        self._criar_tabelas()
        self.carregar()

    def _criar_resumo(self) -> None:
        self.cards_frame = ttk.Frame(self, style="Surface.TFrame")
        self.cards_frame.pack(fill="x", pady=(0, 12))
        self.card_vars = {k: tk.StringVar() for k in ("aberto_receber", "aberto_pagar", "pago_receber", "pago_pagar", "saldo_caixa")}
        labels = [("aberto_receber", "A receber"), ("aberto_pagar", "A pagar"), ("pago_receber", "Recebido"), ("pago_pagar", "Pago"), ("saldo_caixa", "Saldo caixa")]
        for index, (key, label) in enumerate(labels):
            card = ttk.Frame(self.cards_frame, style="Card.TFrame", padding=12)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 8))
            ttk.Label(card, text=label, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=self.card_vars[key], style="CardValue.TLabel").pack(anchor="w")
            self.cards_frame.columnconfigure(index, weight=1)

    def _criar_form_lancamento(self) -> None:
        form = ttk.LabelFrame(self, text="Novo lancamento", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="Tipo").grid(row=0, column=0, padx=(0, 6), pady=4, sticky="w")
        ttk.Combobox(form, textvariable=self.inputs["tipo"], values=["RECEBER", "PAGAR"], width=14, state="readonly").grid(row=0, column=1, padx=(0, 12), pady=4, sticky="ew")
        for index, (name, label) in enumerate([("descricao", "Descricao"), ("valor", "Valor")], start=1):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), pady=4, sticky="w")
            ttk.Entry(form, textvariable=self.inputs[name], width=20).grid(row=0, column=index * 2 + 1, padx=(0, 12), pady=4, sticky="ew")
        ttk.Label(form, text="Vencimento").grid(row=1, column=0, padx=(0, 6), pady=4, sticky="w")
        ttk.Entry(form, textvariable=self.inputs["data_vencimento"], width=14).grid(row=1, column=1, padx=(0, 12), pady=4, sticky="ew")
        ttk.Label(form, text="Cliente").grid(row=1, column=2, padx=(0, 6), pady=4, sticky="w")
        self.cliente_sel = Seletor(form, self.inputs["cliente_id"], self.lookups.clientes, largura=22)
        self.cliente_sel.grid(row=1, column=3, padx=(0, 12), pady=4, sticky="ew")
        ttk.Label(form, text="Fornecedor").grid(row=1, column=4, padx=(0, 6), pady=4, sticky="w")
        self.fornecedor_sel = Seletor(form, self.inputs["fornecedor_id"], self.lookups.fornecedores, largura=22)
        self.fornecedor_sel.grid(row=1, column=5, padx=(0, 12), pady=4, sticky="ew")
        for coluna in (1, 3, 5):
            form.columnconfigure(coluna, weight=1)
        aplicar_permissao(ttk.Button(form, text="Criar lancamento", command=self.criar_lancamento, style="Primary.TButton"), "financeiro", "criar").grid(row=0, column=6, rowspan=2, sticky="e")

    def _criar_form_baixa(self) -> None:
        form = ttk.LabelFrame(self, text="Baixa e estorno", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 12))
        ttk.Label(form, text="Lancamento").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.baixa_inputs["lancamento_id"], width=8, state="readonly").grid(row=0, column=1, padx=(0, 12))
        ttk.Label(form, text="Forma").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Combobox(
            form, textvariable=self.baixa_inputs["forma_pagamento"],
            values=["DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO", "BOLETO", "TRANSFERENCIA"], width=18,
        ).grid(row=0, column=3, padx=(0, 12))
        ttk.Label(form, text="Data pagamento").grid(row=0, column=4, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.baixa_inputs["data_pagamento"], width=14).grid(row=0, column=5, padx=(0, 12))
        aplicar_permissao(ttk.Button(form, text="Baixar", command=self.baixar_lancamento, style="Primary.TButton"), "financeiro", "editar").grid(row=0, column=6, padx=(0, 8))
        aplicar_permissao(ttk.Button(form, text="Estornar", command=self.estornar_lancamento), "financeiro", "excluir").grid(row=0, column=7)

    def _criar_tabelas(self) -> None:
        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True)
        lanc_frame = ttk.LabelFrame(panes, text="Lancamentos", padding=10, style="Section.TLabelframe")
        caixa_frame = ttk.LabelFrame(panes, text="Caixa", padding=10, style="Section.TLabelframe")
        panes.add(lanc_frame, weight=3)
        panes.add(caixa_frame, weight=2)

        self.lanc_tabela = TabelaFiltravel(
            lanc_frame,
            ["id", "tipo", "origem", "descricao", "parte", "valor", "data_vencimento", "data_pagamento", "status"],
            altura=8,
            larguras={"id": 50, "descricao": 200, "parte": 160},
        )
        self.lanc_tabela.pack(fill="both", expand=True)
        self.lanc_tabela.ao_selecionar(self._selecionar_lancamento)

        self.caixa_tabela = TabelaFiltravel(
            caixa_frame, ["id", "tipo", "descricao", "valor", "forma_pagamento", "criado_em"], altura=6, larguras={"id": 50, "descricao": 240}
        )
        self.caixa_tabela.pack(fill="both", expand=True)

    def _lancamento_id(self) -> int:
        valor = self.baixa_inputs["lancamento_id"].get()
        if not valor:
            raise ValueError("Selecione um lancamento na tabela.")
        return int(valor)

    def criar_lancamento(self) -> None:
        try:
            dados = {name: var.get() for name, var in self.inputs.items()}
            dados["origem"] = "MANUAL"
            dados["origem_id"] = 0
            self.controller.criar_lancamento(dados)
            self.carregar()
            messagebox.showinfo("Financeiro", "Lancamento criado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def baixar_lancamento(self) -> None:
        try:
            self.controller.baixar_lancamento(
                self._lancamento_id(),
                self.baixa_inputs["forma_pagamento"].get(),
                usuario_id=self.usuario.id,
                data_pagamento=self.baixa_inputs["data_pagamento"].get(),
            )
            self.carregar()
            messagebox.showinfo("Financeiro", "Lancamento baixado e caixa movimentado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def estornar_lancamento(self) -> None:
        try:
            self.controller.estornar_lancamento(self._lancamento_id(), usuario_id=self.usuario.id)
            self.carregar()
            messagebox.showinfo("Financeiro", "Lancamento estornado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        try:
            resumo = self.controller.resumo_fluxo()
            lancamentos = self.controller.listar_lancamentos()
            caixa = self.controller.listar_caixa()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        for key, value in resumo.items():
            if key in self.card_vars:
                self.card_vars[key].set(f"R$ {format_value(value)}")

        def parte(item) -> str:
            if getattr(item, "cliente", None):
                return item.cliente.nome
            if getattr(item, "fornecedor", None):
                return item.fornecedor.razao_social
            return ""

        self.lanc_tabela.preencher(
            [
                (i.id, [i.id, i.tipo, i.origem, i.descricao, parte(i), i.valor, i.data_vencimento, i.data_pagamento, i.status])
                for i in lancamentos
            ]
        )
        self.caixa_tabela.preencher(
            [(i.id, [i.id, i.tipo, i.descricao, i.valor, i.forma_pagamento, i.criado_em]) for i in caixa]
        )
        self.cliente_sel.recarregar()
        self.fornecedor_sel.recarregar()

    def _selecionar_lancamento(self, _event) -> None:
        selection = self.lanc_tabela.selection()
        if selection:
            self.baixa_inputs["lancamento_id"].set(selection[0])
