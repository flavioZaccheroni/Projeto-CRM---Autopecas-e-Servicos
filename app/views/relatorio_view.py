import tkinter as tk
from tkinter import messagebox, ttk

from app.controllers.relatorio_controller import RelatorioController


class RelatorioFrame(ttk.Frame):
    def __init__(self, master) -> None:
        super().__init__(master, padding=22, style="Surface.TFrame")
        self.controller = RelatorioController()
        self.tipo = tk.StringVar(value="vendas")
        self.formato = tk.StringVar(value="pdf")
        self.ultimo_arquivo = tk.StringVar(value="")

        ttk.Label(self, text="Relatorios", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            self,
            text="Exporte relatorios operacionais em PDF ou Excel para vendas, estoque, OS e financeiro.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 14))

        form = ttk.LabelFrame(self, text="Geracao de relatorio", padding=16, style="Section.TLabelframe")
        form.pack(fill="x", pady=(0, 12))
        ttk.Label(form, text="Tipo").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Combobox(
            form,
            textvariable=self.tipo,
            values=["vendas", "estoque", "os", "financeiro"],
            state="readonly",
            width=20,
        ).grid(row=0, column=1, sticky="w", padx=(0, 18))
        ttk.Label(form, text="Formato").grid(row=0, column=2, sticky="w", padx=(0, 8))
        ttk.Combobox(
            form,
            textvariable=self.formato,
            values=["pdf", "xlsx"],
            state="readonly",
            width=12,
        ).grid(row=0, column=3, sticky="w", padx=(0, 18))
        ttk.Button(form, text="Gerar relatorio", command=self.gerar, style="Primary.TButton").grid(row=0, column=4, sticky="e")
        form.columnconfigure(4, weight=1)

        result = ttk.LabelFrame(self, text="Ultimo arquivo gerado", padding=16, style="Section.TLabelframe")
        result.pack(fill="x")
        ttk.Label(result, textvariable=self.ultimo_arquivo, style="Subtle.TLabel", wraplength=900).pack(anchor="w")

        info = ttk.LabelFrame(self, text="Conteudo por relatorio", padding=16, style="Section.TLabelframe")
        info.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(
            info,
            text=(
                "Vendas: numero, cliente, status e valor. "
                "Estoque: produto, saldo e localizacao. "
                "OS: cliente, veiculo, status e valor. "
                "Financeiro: lancamentos e movimentacoes de caixa."
            ),
            style="Subtle.TLabel",
            wraplength=900,
        ).pack(anchor="w")

    def gerar(self) -> None:
        try:
            arquivo = self.controller.gerar(self.tipo.get(), self.formato.get())
            self.ultimo_arquivo.set(str(arquivo))
            messagebox.showinfo("Relatorios", f"Relatorio gerado:\n{arquivo}")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
