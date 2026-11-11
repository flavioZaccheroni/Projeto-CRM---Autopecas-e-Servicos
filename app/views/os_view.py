import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.lookup_controller import LookupController
from app.controllers.os_controller import OrdemServicoController
from app.views.helpers import FORMAS_PAGAMENTO, ItensPanel, abrir_arquivo, aplicar_permissao, executar, pedir_motivo
from app.views.widgets import IdVar, Seletor, TabelaFiltravel


class OrdemServicoFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = OrdemServicoController()
        self.lookups = LookupController()
        self.os_inputs = {
            "cliente_id": IdVar(),
            "veiculo_id": IdVar(),
            "numero": tk.StringVar(),
            "data_abertura": tk.StringVar(),
            "status": tk.StringVar(value="ABERTA"),
            "defeito_relatado": tk.StringVar(),
            "diagnostico": tk.StringVar(),
        }
        self.item_inputs = {
            "os_id": tk.StringVar(),
            "tipo": tk.StringVar(value="PECA"),
            "produto_id": IdVar(),
            "descricao": tk.StringVar(),
            "quantidade": tk.StringVar(value="1"),
            "valor_unitario": tk.StringVar(),
        }
        self.fin_inputs = {
            "data_vencimento": tk.StringVar(),
            "parcelas": tk.StringVar(value="1"),
            "forma_pagamento": tk.StringVar(),
        }

        ttk.Label(self, text="Ordem de Servico", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Abra OS, registre pecas e mao de obra, finalize com baixa de estoque e financeiro, e imprima em PDF. Numero em branco = automatico.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 10))
        self._criar_form_os()
        self._criar_form_item()
        self._criar_form_finalizacao()
        self.itens_panel = ItensPanel(
            self,
            ["id", "tipo", "produto.descricao", "descricao", "quantidade", "valor_unitario", "valor_total"],
            self.controller.listar_itens,
            self.controller.atualizar_item,
            self.controller.remover_item,
            lambda: (self.item_inputs["quantidade"].get(), self.item_inputs["valor_unitario"].get()),
            "os",
            self.carregar,
        )
        self.itens_panel.pack(fill="x", pady=(0, 8))
        table_frame = ttk.LabelFrame(self, text="Ordens de servico", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        self.tabela = TabelaFiltravel(
            table_frame,
            ["id", "numero", "cliente", "veiculo", "data_abertura", "status", "parcelas", "valor_total"],
            altura=6,
            larguras={"id": 50, "numero": 100, "cliente": 170, "veiculo": 100},
        )
        self.tabela.pack(fill="both", expand=True)
        self.tabela.ao_selecionar(self._selecionar)
        self.carregar()

    def _criar_form_os(self) -> None:
        form = ttk.LabelFrame(self, text="Abertura e diagnostico", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="Cliente").grid(row=0, column=0, padx=(0, 6), pady=3, sticky="w")
        self.cliente_sel = Seletor(form, self.os_inputs["cliente_id"], self.lookups.clientes, largura=28, ao_escolher=self._cliente_escolhido)
        self.cliente_sel.grid(row=0, column=1, padx=(0, 10), pady=3, sticky="ew")
        ttk.Label(form, text="Veiculo").grid(row=0, column=2, padx=(0, 6), pady=3, sticky="w")
        self.veiculo_sel = Seletor(form, self.os_inputs["veiculo_id"], lambda: self.lookups.veiculos(self.os_inputs["cliente_id"].get() or None), largura=28)
        self.veiculo_sel.grid(row=0, column=3, padx=(0, 10), pady=3, sticky="ew")
        extras = [("numero", "Numero (auto)"), ("data_abertura", "Data/hora ISO"), ("status", "Status"), ("defeito_relatado", "Defeito"), ("diagnostico", "Diagnostico")]
        for index, (name, label) in enumerate(extras):
            linha, coluna = divmod(index + 2, 4)
            ttk.Label(form, text=label).grid(row=linha, column=coluna * 2, padx=(0, 6), pady=3, sticky="w")
            ttk.Entry(form, textvariable=self.os_inputs[name], width=22).grid(row=linha, column=coluna * 2 + 1, padx=(0, 10), pady=3, sticky="ew")
        for coluna in (1, 3, 5, 7):
            form.columnconfigure(coluna, weight=1)
        aplicar_permissao(ttk.Button(form, text="Abrir OS", command=self.abrir_os, style="Primary.TButton"), "os", "criar").grid(row=2, column=6, columnspan=2, sticky="e")

    def _cliente_escolhido(self, _opcao) -> None:
        """Ao trocar o cliente, a lista de veiculos passa a mostrar so os dele."""
        self.os_inputs["veiculo_id"].set("")
        self.veiculo_sel.recarregar()

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens (selecione uma OS na tabela)", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        ttk.Label(form, text="OS").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.item_inputs["os_id"], width=8, state="readonly").grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Tipo").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Combobox(form, textvariable=self.item_inputs["tipo"], values=["PECA", "SERVICO"], width=10, state="readonly").grid(row=0, column=3, padx=(0, 10))
        ttk.Label(form, text="Produto (pecas)").grid(row=0, column=4, padx=(0, 6), sticky="w")
        self.produto_sel = Seletor(form, self.item_inputs["produto_id"], self.lookups.produtos, largura=32, ao_escolher=self._produto_escolhido)
        self.produto_sel.grid(row=0, column=5, padx=(0, 10), sticky="ew")
        ttk.Label(form, text="Descricao").grid(row=1, column=0, padx=(0, 6), pady=3, sticky="w")
        ttk.Entry(form, textvariable=self.item_inputs["descricao"], width=30).grid(row=1, column=1, columnspan=3, padx=(0, 10), pady=3, sticky="ew")
        ttk.Label(form, text="Qtd").grid(row=1, column=4, padx=(0, 6), sticky="e")
        qtd = ttk.Frame(form, style="Surface.TFrame")
        qtd.grid(row=1, column=5, sticky="w")
        ttk.Entry(qtd, textvariable=self.item_inputs["quantidade"], width=8).pack(side="left", padx=(0, 10))
        ttk.Label(qtd, text="Valor unitario").pack(side="left", padx=(0, 6))
        ttk.Entry(qtd, textvariable=self.item_inputs["valor_unitario"], width=12).pack(side="left")
        form.columnconfigure(5, weight=1)
        aplicar_permissao(ttk.Button(form, text="Adicionar item", command=self.adicionar_item), "os", "criar").grid(row=1, column=6, padx=(10, 0))

    def _produto_escolhido(self, opcao) -> None:
        if not opcao:
            return
        if opcao[2]:
            self.item_inputs["valor_unitario"].set(opcao[2])
        if not self.item_inputs["descricao"].get():
            self.item_inputs["descricao"].set(opcao[1].split(" - ", 1)[-1])

    def _criar_form_finalizacao(self) -> None:
        form = ttk.LabelFrame(self, text="Finalizacao, cancelamento e impressao", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="1o vencimento").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.fin_inputs["data_vencimento"], width=12).grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Parcelas").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Spinbox(form, from_=1, to=60, textvariable=self.fin_inputs["parcelas"], width=5).grid(row=0, column=3, padx=(0, 10))
        ttk.Label(form, text="Pagamento").grid(row=0, column=4, padx=(0, 6), sticky="w")
        ttk.Combobox(form, textvariable=self.fin_inputs["forma_pagamento"], values=FORMAS_PAGAMENTO, width=14).grid(row=0, column=5, padx=(0, 12))
        aplicar_permissao(ttk.Button(form, text="Finalizar OS", command=self.finalizar_os, style="Primary.TButton"), "os", "editar").grid(row=0, column=6, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Cancelar OS", command=self.cancelar), "os", "excluir").grid(row=0, column=7, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="PDF", command=self.imprimir), "os", "ver").grid(row=0, column=8)

    def _os_id(self) -> int:
        valor = self.item_inputs["os_id"].get()
        if not valor:
            raise ValueError("Selecione uma OS na tabela.")
        return int(valor)

    def abrir_os(self) -> None:
        executar(
            lambda: self.controller.abrir_os({n: v.get() for n, v in self.os_inputs.items()}, usuario_id=self.usuario.id),
            "OS aberta com sucesso.", "Ordem de Servico", self.carregar,
        )

    def adicionar_item(self) -> None:
        executar(
            lambda: self.controller.adicionar_item({"os_id": self._os_id(), **{n: v.get() for n, v in self.item_inputs.items() if n != "os_id"}}),
            "Item adicionado.", "Ordem de Servico",
            lambda: (self.carregar(), self.itens_panel.mostrar(self.item_inputs["os_id"].get())),
        )

    def finalizar_os(self) -> None:
        executar(
            lambda: self.controller.finalizar_os(
                self._os_id(),
                usuario_id=self.usuario.id,
                data_vencimento=self.fin_inputs["data_vencimento"].get(),
                parcelas=self.fin_inputs["parcelas"].get(),
                forma_pagamento=self.fin_inputs["forma_pagamento"].get(),
            ),
            "OS finalizada, estoque baixado e financeiro gerado.", "Ordem de Servico", self.carregar,
        )

    def cancelar(self) -> None:
        motivo = pedir_motivo(self, "Cancelar OS", "Motivo do cancelamento (estoque e financeiro serao estornados):")
        if motivo:
            executar(
                lambda: self.controller.cancelar_os(self._os_id(), motivo, usuario_id=self.usuario.id),
                "OS cancelada.", "Ordem de Servico", self.carregar,
            )

    def imprimir(self) -> None:
        try:
            arquivo = self.controller.imprimir_os(self._os_id())
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        abrir_arquivo(arquivo)
        messagebox.showinfo("Ordem de Servico", f"PDF gerado:\n{arquivo}")

    def carregar(self) -> None:
        try:
            ordens = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.tabela.preencher(
            [
                (o.id, [o.id, o.numero, o.cliente.nome if o.cliente else "", o.veiculo.placa if o.veiculo else "", o.data_abertura, o.status, o.parcelas, o.valor_total])
                for o in ordens
            ]
        )
        self.cliente_sel.recarregar()
        self.veiculo_sel.recarregar()
        self.produto_sel.recarregar()

    def _selecionar(self, _event) -> None:
        selection = self.tabela.selection()
        if selection:
            self.item_inputs["os_id"].set(selection[0])
            self.itens_panel.mostrar(selection[0])
