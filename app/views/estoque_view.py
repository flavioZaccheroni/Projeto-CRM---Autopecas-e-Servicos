import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.estoque_controller import EstoqueController
from app.controllers.lookup_controller import LookupController
from app.views.helpers import aplicar_permissao
from app.views.widgets import IdVar, Seletor, TabelaFiltravel


def _nome_produto(item) -> str:
    produto = getattr(item, "produto", None)
    return f"{produto.codigo} - {produto.descricao}" if produto else ""


class EstoqueFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = EstoqueController()
        lookups = LookupController()
        self.inputs = {
            "produto_id": IdVar(),
            "tipo": tk.StringVar(value="ENTRADA"),
            "quantidade": tk.StringVar(),
            "origem": tk.StringVar(value="MANUAL"),
            "localizacao": tk.StringVar(),
        }

        ttk.Label(self, text="Estoque", style="Header.TLabel").pack(anchor="w")
        ttk.Label(self, text="Controle saldo, entradas, saidas e ajustes com historico de movimentacao. Ctrl+F busca na tabela.", style="Subtle.TLabel").pack(anchor="w", pady=(4, 14))
        form = ttk.LabelFrame(self, text="Movimento de estoque", padding=14, style="Section.TLabelframe")
        form.pack(fill="x")
        ttk.Label(form, text="Produto").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.produto_sel = Seletor(form, self.inputs["produto_id"], lookups.produtos, largura=34)
        self.produto_sel.grid(row=0, column=1, padx=(0, 12), sticky="ew")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Tipo").grid(row=0, column=2, sticky="w", padx=(0, 6))
        ttk.Combobox(form, textvariable=self.inputs["tipo"], values=["ENTRADA", "SAIDA", "AJUSTE"], width=12, state="readonly").grid(row=0, column=3, padx=(0, 12))
        for index, (name, label) in enumerate([("quantidade", "Quantidade"), ("origem", "Origem"), ("localizacao", "Localizacao")], start=2):
            ttk.Label(form, text=label).grid(row=0, column=index * 2, sticky="w", padx=(0, 6))
            ttk.Entry(form, textvariable=self.inputs[name], width=14).grid(row=0, column=index * 2 + 1, padx=(0, 12))

        actions = ttk.Frame(self, style="Surface.TFrame")
        actions.pack(fill="x", pady=12)
        aplicar_permissao(ttk.Button(actions, text="Registrar movimento", command=self.movimentar, style="Primary.TButton"), "estoque", "criar").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Atualizar", command=self.carregar).pack(side="left")

        saldo_frame = ttk.LabelFrame(self, text="Saldo atual", padding=10, style="Section.TLabelframe")
        saldo_frame.pack(fill="both", expand=True, pady=(0, 12))
        self.saldo_tabela = TabelaFiltravel(
            saldo_frame, ["id", "produto", "quantidade_atual", "localizacao"], altura=6, larguras={"id": 50, "produto": 320}
        )
        self.saldo_tabela.pack(fill="both", expand=True)

        mov_frame = ttk.LabelFrame(self, text="Movimentacoes", padding=10, style="Section.TLabelframe")
        mov_frame.pack(fill="both", expand=True)
        self.mov_tabela = TabelaFiltravel(
            mov_frame,
            ["id", "produto", "tipo", "origem", "quantidade", "saldo_anterior", "saldo_posterior"],
            altura=7,
            larguras={"id": 50, "produto": 280},
        )
        self.mov_tabela.pack(fill="both", expand=True)
        self.carregar()

    def movimentar(self) -> None:
        try:
            self.controller.movimentar({name: var.get() for name, var in self.inputs.items()}, usuario_id=self.usuario.id)
            self.carregar()
            messagebox.showinfo("Estoque", "Movimento registrado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        try:
            saldos = self.controller.listar()
            movimentos = self.controller.listar_movimentacoes()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.saldo_tabela.preencher([(i.id, [i.id, _nome_produto(i), i.quantidade_atual, i.localizacao]) for i in saldos])
        self.mov_tabela.preencher(
            [(i.id, [i.id, _nome_produto(i), i.tipo, i.origem, i.quantidade, i.saldo_anterior, i.saldo_posterior]) for i in movimentos]
        )
        self.produto_sel.recarregar()
