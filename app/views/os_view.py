import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.os_controller import OrdemServicoController
from app.views.helpers import FORMAS_PAGAMENTO, ItensPanel, abrir_arquivo, aplicar_permissao, executar, pedir_motivo
from app.views.theme import format_value


class OrdemServicoFrame(ttk.Frame):
    def __init__(self, master, usuario) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.usuario = usuario
        self.controller = OrdemServicoController()
        self.os_inputs = {
            "cliente_id": tk.StringVar(),
            "veiculo_id": tk.StringVar(),
            "numero": tk.StringVar(),
            "data_abertura": tk.StringVar(),
            "status": tk.StringVar(value="ABERTA"),
            "defeito_relatado": tk.StringVar(),
            "diagnostico": tk.StringVar(),
        }
        self.item_inputs = {
            "os_id": tk.StringVar(),
            "tipo": tk.StringVar(value="PECA"),
            "produto_id": tk.StringVar(),
            "descricao": tk.StringVar(),
            "quantidade": tk.StringVar(),
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
            ["id", "tipo", "produto_id", "descricao", "quantidade", "valor_unitario", "valor_total"],
            self.controller.listar_itens,
            self.controller.atualizar_item,
            self.controller.remover_item,
            lambda: (self.item_inputs["quantidade"].get(), self.item_inputs["valor_unitario"].get()),
            "os",
            self.carregar,
        )
        self.itens_panel.pack(fill="x", pady=(0, 8))
        self._criar_tabela()
        self.carregar()

    def _criar_form_os(self) -> None:
        form = ttk.LabelFrame(self, text="Abertura e diagnostico", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        fields = [
            ("cliente_id", "Cliente ID"),
            ("veiculo_id", "Veiculo ID"),
            ("numero", "Numero (auto)"),
            ("data_abertura", "Data/hora ISO"),
            ("status", "Status"),
            ("defeito_relatado", "Defeito"),
            ("diagnostico", "Diagnostico"),
        ]
        for index, (name, label) in enumerate(fields):
            row = index // 4
            col = (index % 4) * 2
            ttk.Label(form, text=label).grid(row=row, column=col, padx=(0, 6), pady=3, sticky="w")
            ttk.Entry(form, textvariable=self.os_inputs[name], width=16).grid(row=row, column=col + 1, padx=(0, 10), pady=3, sticky="ew")
            form.columnconfigure(col + 1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Abrir OS", command=self.abrir_os, style="Primary.TButton"), "os", "criar").grid(row=1, column=6, columnspan=2, sticky="e")

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 6))
        fields = [
            ("os_id", "OS ID"),
            ("tipo", "Tipo"),
            ("produto_id", "Produto ID"),
            ("descricao", "Descricao"),
            ("quantidade", "Quantidade"),
            ("valor_unitario", "Valor unitario"),
        ]
        for index, (name, label) in enumerate(fields):
            row = index // 4
            col = (index % 4) * 2
            ttk.Label(form, text=label).grid(row=row, column=col, padx=(0, 6), pady=3, sticky="w")
            if name == "tipo":
                widget = ttk.Combobox(form, textvariable=self.item_inputs[name], values=["PECA", "SERVICO"], width=14)
            else:
                widget = ttk.Entry(form, textvariable=self.item_inputs[name], width=16)
            widget.grid(row=row, column=col + 1, padx=(0, 10), pady=3, sticky="ew")
            form.columnconfigure(col + 1, weight=1)
        aplicar_permissao(ttk.Button(form, text="Adicionar item", command=self.adicionar_item), "os", "criar").grid(row=1, column=6, columnspan=2, sticky="e")

    def _criar_form_finalizacao(self) -> None:
        form = ttk.LabelFrame(self, text="Finalizacao, cancelamento e impressao", padding=12, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="1o vencimento").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Entry(form, textvariable=self.fin_inputs["data_vencimento"], width=12).grid(row=0, column=1, padx=(0, 10))
        ttk.Label(form, text="Parcelas").grid(row=0, column=2, padx=(0, 6), sticky="w")
        ttk.Spinbox(form, from_=1, to=60, textvariable=self.fin_inputs["parcelas"], width=5).grid(row=0, column=3, padx=(0, 10))
        ttk.Label(form, text="Pagamento").grid(row=0, column=4, padx=(0, 6), sticky="w")
        ttk.Combobox(form, textvariable=self.fin_inputs["forma_pagamento"], values=FORMAS_PAGAMENTO, width=16).grid(row=0, column=5, padx=(0, 12))
        aplicar_permissao(ttk.Button(form, text="Finalizar OS", command=self.finalizar_os, style="Primary.TButton"), "os", "editar").grid(row=0, column=6, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Cancelar OS", command=self.cancelar), "os", "excluir").grid(row=0, column=7, padx=(0, 6))
        aplicar_permissao(ttk.Button(form, text="Imprimir PDF", command=self.imprimir), "os", "ver").grid(row=0, column=8)

    def _criar_tabela(self) -> None:
        table_frame = ttk.LabelFrame(self, text="Ordens de servico", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        columns = ["id", "cliente_id", "veiculo_id", "numero", "data_abertura", "status", "parcelas", "valor_total"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)
        for column in columns:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=120, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)

    def _os_id(self) -> int:
        return int(self.item_inputs["os_id"].get())

    def abrir_os(self) -> None:
        executar(
            lambda: self.controller.abrir_os({n: v.get() for n, v in self.os_inputs.items()}, usuario_id=self.usuario.id),
            "OS aberta com sucesso.", "Ordem de Servico", self.carregar,
        )

    def adicionar_item(self) -> None:
        executar(
            lambda: self.controller.adicionar_item({n: v.get() for n, v in self.item_inputs.items()}),
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
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            ordens = self.controller.listar()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return
        for o in ordens:
            self.tree.insert(
                "", "end", iid=str(o.id),
                values=[format_value(x) for x in (o.id, o.cliente_id, o.veiculo_id, o.numero, o.data_abertura, o.status, o.parcelas, o.valor_total)],
            )

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["os_id"].set(selection[0])
            self.itens_panel.mostrar(selection[0])
