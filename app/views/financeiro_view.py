import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.financeiro_controller import FinanceiroController
from app.views.theme import format_value


class FinanceiroFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = FinanceiroController()
        self.inputs = {
            "tipo": tk.StringVar(value="RECEBER"),
            "descricao": tk.StringVar(),
            "valor": tk.StringVar(),
            "data_vencimento": tk.StringVar(),
            "cliente_id": tk.StringVar(),
            "fornecedor_id": tk.StringVar(),
        }
        self.baixa_inputs = {
            "lancamento_id": tk.StringVar(),
            "forma_pagamento": tk.StringVar(value="DINHEIRO"),
            "data_pagamento": tk.StringVar(),
        }

        ttk.Label(self, text="Financeiro", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Controle contas a pagar e receber, baixa de pagamentos, estornos e movimentacoes de caixa.",
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
        self.card_vars = {
            "aberto_receber": tk.StringVar(),
            "aberto_pagar": tk.StringVar(),
            "pago_receber": tk.StringVar(),
            "pago_pagar": tk.StringVar(),
            "saldo_caixa": tk.StringVar(),
        }
        labels = [
            ("aberto_receber", "A receber"),
            ("aberto_pagar", "A pagar"),
            ("pago_receber", "Recebido"),
            ("pago_pagar", "Pago"),
            ("saldo_caixa", "Saldo caixa"),
        ]
        for index, (key, label) in enumerate(labels):
            card = ttk.LabelFrame(self.cards_frame, text=label, padding=10, style="Section.TLabelframe")
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 8))
            ttk.Label(card, textvariable=self.card_vars[key], font=("Segoe UI", 14, "bold")).pack(anchor="w")
            self.cards_frame.columnconfigure(index, weight=1)

    def _criar_form_lancamento(self) -> None:
        form = ttk.LabelFrame(self, text="Novo lancamento", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        fields = [
            ("tipo", "Tipo"),
            ("descricao", "Descricao"),
            ("valor", "Valor"),
            ("data_vencimento", "Vencimento"),
            ("cliente_id", "Cliente ID"),
            ("fornecedor_id", "Fornecedor ID"),
        ]
        for index, (name, label) in enumerate(fields):
            row = index // 3
            col = (index % 3) * 2
            ttk.Label(form, text=label).grid(row=row, column=col, padx=(0, 6), pady=4, sticky="w")
            if name == "tipo":
                widget = ttk.Combobox(form, textvariable=self.inputs[name], values=["RECEBER", "PAGAR"], width=18)
            else:
                widget = ttk.Entry(form, textvariable=self.inputs[name], width=20)
            widget.grid(row=row, column=col + 1, padx=(0, 12), pady=4, sticky="ew")
            form.columnconfigure(col + 1, weight=1)
        ttk.Button(form, text="Criar lancamento", command=self.criar_lancamento, style="Primary.TButton").grid(row=1, column=6, sticky="e")

    def _criar_form_baixa(self) -> None:
        form = ttk.LabelFrame(self, text="Baixa e estorno", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 12))
        fields = [
            ("lancamento_id", "Lancamento ID"),
            ("forma_pagamento", "Forma"),
            ("data_pagamento", "Data pagamento"),
        ]
        for index, (name, label) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, padx=(0, 6), sticky="w")
            ttk.Entry(form, textvariable=self.baixa_inputs[name], width=18).grid(row=0, column=index * 2 + 1, padx=(0, 12), sticky="ew")
            form.columnconfigure(index * 2 + 1, weight=1)
        ttk.Button(form, text="Baixar", command=self.baixar_lancamento, style="Primary.TButton").grid(row=0, column=6, padx=(0, 8))
        ttk.Button(form, text="Estornar", command=self.estornar_lancamento).grid(row=0, column=7)

    def _criar_tabelas(self) -> None:
        panes = ttk.PanedWindow(self, orient="vertical")
        panes.pack(fill="both", expand=True)

        lanc_frame = ttk.LabelFrame(panes, text="Lancamentos", padding=10, style="Section.TLabelframe")
        caixa_frame = ttk.LabelFrame(panes, text="Caixa", padding=10, style="Section.TLabelframe")
        panes.add(lanc_frame, weight=3)
        panes.add(caixa_frame, weight=2)

        lanc_cols = ["id", "tipo", "origem", "descricao", "valor", "data_vencimento", "data_pagamento", "status"]
        self.lanc_tree = ttk.Treeview(lanc_frame, columns=lanc_cols, show="headings", height=9)
        for column in lanc_cols:
            self.lanc_tree.heading(column, text=column.replace("_", " ").title())
            self.lanc_tree.column(column, width=130, anchor="w")
        lanc_scroll = ttk.Scrollbar(lanc_frame, orient="vertical", command=self.lanc_tree.yview)
        self.lanc_tree.configure(yscrollcommand=lanc_scroll.set)
        self.lanc_tree.grid(row=0, column=0, sticky="nsew")
        lanc_scroll.grid(row=0, column=1, sticky="ns")
        lanc_frame.columnconfigure(0, weight=1)
        lanc_frame.rowconfigure(0, weight=1)
        self.lanc_tree.bind("<<TreeviewSelect>>", self._selecionar_lancamento)

        caixa_cols = ["id", "tipo", "descricao", "valor", "forma_pagamento", "criado_em"]
        self.caixa_tree = ttk.Treeview(caixa_frame, columns=caixa_cols, show="headings", height=7)
        for column in caixa_cols:
            self.caixa_tree.heading(column, text=column.replace("_", " ").title())
            self.caixa_tree.column(column, width=140, anchor="w")
        caixa_scroll = ttk.Scrollbar(caixa_frame, orient="vertical", command=self.caixa_tree.yview)
        self.caixa_tree.configure(yscrollcommand=caixa_scroll.set)
        self.caixa_tree.grid(row=0, column=0, sticky="nsew")
        caixa_scroll.grid(row=0, column=1, sticky="ns")
        caixa_frame.columnconfigure(0, weight=1)
        caixa_frame.rowconfigure(0, weight=1)

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
                int(self.baixa_inputs["lancamento_id"].get()),
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
            self.controller.estornar_lancamento(
                int(self.baixa_inputs["lancamento_id"].get()),
                usuario_id=self.usuario.id,
            )
            self.carregar()
            messagebox.showinfo("Financeiro", "Lancamento estornado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for tree in [self.lanc_tree, self.caixa_tree]:
            for row in tree.get_children():
                tree.delete(row)

        resumo = self.controller.resumo_fluxo()
        for key, value in resumo.items():
            self.card_vars[key].set(f"R$ {value}")

        for item in self.controller.listar_lancamentos():
            self.lanc_tree.insert(
                "",
                "end",
                iid=str(item.id),
                values=[
                    format_value(item.id),
                    format_value(item.tipo),
                    format_value(item.origem),
                    format_value(item.descricao),
                    format_value(item.valor),
                    format_value(item.data_vencimento),
                    format_value(item.data_pagamento),
                    format_value(item.status),
                ],
            )
        for item in self.controller.listar_caixa():
            self.caixa_tree.insert(
                "",
                "end",
                values=[
                    format_value(item.id),
                    format_value(item.tipo),
                    format_value(item.descricao),
                    format_value(item.valor),
                    format_value(item.forma_pagamento),
                    format_value(item.criado_em),
                ],
            )

    def _selecionar_lancamento(self, _event) -> None:
        selection = self.lanc_tree.selection()
        if selection:
            self.baixa_inputs["lancamento_id"].set(selection[0])
