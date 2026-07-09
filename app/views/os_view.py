import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.os_controller import OrdemServicoController
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
            "data_vencimento": tk.StringVar(),
        }

        ttk.Label(self, text="Ordem de Servico", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Abra OS, registre pecas e mao de obra, finalize com baixa de estoque e financeiro a receber.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 14))
        self._criar_form_os()
        self._criar_form_item()
        self._criar_tabela()
        self.carregar()

    def _criar_form_os(self) -> None:
        form = ttk.LabelFrame(self, text="Abertura e diagnostico", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 8))
        fields = [
            ("cliente_id", "Cliente ID"),
            ("veiculo_id", "Veiculo ID"),
            ("numero", "Numero"),
            ("data_abertura", "Data/hora ISO"),
            ("status", "Status"),
            ("defeito_relatado", "Defeito"),
            ("diagnostico", "Diagnostico"),
        ]
        for index, (name, label) in enumerate(fields):
            row = index // 4
            col = (index % 4) * 2
            ttk.Label(form, text=label).grid(row=row, column=col, padx=(0, 6), pady=4, sticky="w")
            ttk.Entry(form, textvariable=self.os_inputs[name], width=18).grid(row=row, column=col + 1, padx=(0, 12), pady=4, sticky="ew")
            form.columnconfigure(col + 1, weight=1)
        ttk.Button(form, text="Abrir OS", command=self.abrir_os, style="Primary.TButton").grid(row=1, column=6, columnspan=2, sticky="e")

    def _criar_form_item(self) -> None:
        form = ttk.LabelFrame(self, text="Itens e finalizacao", padding=14, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 12))
        fields = [
            ("os_id", "OS ID"),
            ("tipo", "Tipo"),
            ("produto_id", "Produto ID"),
            ("descricao", "Descricao"),
            ("quantidade", "Quantidade"),
            ("valor_unitario", "Valor unitario"),
            ("data_vencimento", "Vencimento"),
        ]
        for index, (name, label) in enumerate(fields):
            row = index // 4
            col = (index % 4) * 2
            ttk.Label(form, text=label).grid(row=row, column=col, padx=(0, 6), pady=4, sticky="w")
            if name == "tipo":
                widget = ttk.Combobox(form, textvariable=self.item_inputs[name], values=["PECA", "SERVICO"], width=16)
            else:
                widget = ttk.Entry(form, textvariable=self.item_inputs[name], width=16)
            widget.grid(row=row, column=col + 1, padx=(0, 12), pady=4, sticky="ew")
            form.columnconfigure(col + 1, weight=1)
        ttk.Button(form, text="Adicionar item", command=self.adicionar_item).grid(row=1, column=6, sticky="e", padx=(0, 8))
        ttk.Button(form, text="Finalizar OS", command=self.finalizar_os).grid(row=1, column=7, sticky="e")

    def _criar_tabela(self) -> None:
        table_frame = ttk.LabelFrame(self, text="Ordens de servico", padding=10, style="Section.TLabelframe")
        table_frame.pack(fill="both", expand=True)
        columns = ["id", "cliente_id", "veiculo_id", "numero", "data_abertura", "status", "valor_total"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        for column in columns:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=135, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._selecionar)

    def abrir_os(self) -> None:
        try:
            self.controller.abrir_os(
                {name: var.get() for name, var in self.os_inputs.items()},
                usuario_id=self.usuario.id,
            )
            self.carregar()
            messagebox.showinfo("Ordem de Servico", "OS aberta com sucesso.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def adicionar_item(self) -> None:
        try:
            self.controller.adicionar_item({name: var.get() for name, var in self.item_inputs.items()})
            self.carregar()
            messagebox.showinfo("Ordem de Servico", "Item adicionado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def finalizar_os(self) -> None:
        try:
            self.controller.finalizar_os(
                int(self.item_inputs["os_id"].get()),
                usuario_id=self.usuario.id,
                data_vencimento=self.item_inputs["data_vencimento"].get(),
            )
            self.carregar()
            messagebox.showinfo("Ordem de Servico", "OS finalizada, estoque baixado e financeiro gerado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def carregar(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.controller.listar():
            self.tree.insert(
                "",
                "end",
                iid=str(item.id),
                values=[
                    format_value(item.id),
                    format_value(item.cliente_id),
                    format_value(item.veiculo_id),
                    format_value(item.numero),
                    format_value(item.data_abertura),
                    format_value(item.status),
                    format_value(item.valor_total),
                ],
            )

    def _selecionar(self, _event) -> None:
        selection = self.tree.selection()
        if selection:
            self.item_inputs["os_id"].set(selection[0])
