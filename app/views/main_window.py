import tkinter as tk
from tkinter import ttk

from app.config.settings import APP_NAME
from app.views.compra_view import CompraFrame
from app.views.crud_view import CrudFrame
from app.views.estoque_view import EstoqueFrame
from app.views.module_configs import CADASTRO_MODULES
from app.views.venda_view import VendaFrame


class MainWindow:
    def __init__(self, usuario) -> None:
        self.usuario = usuario
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1160x680")

        sidebar = tk.Frame(self.root, width=220, bg="#263238")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="ERP Autopecas",
            fg="white",
            bg="#263238",
            font=("Segoe UI", 13, "bold"),
            pady=18,
        ).pack(fill="x")

        menu_items = [
            "Dashboard",
            "Clientes",
            "Veiculos",
            "Fornecedores",
            "Categorias",
            "Marcas",
            "Produtos",
            "Estoque",
            "Compras",
            "Vendas",
            "Usuarios",
            "Permissoes",
            "Configuracoes",
        ]
        for modulo in menu_items:
            tk.Button(
                sidebar,
                text=modulo,
                anchor="w",
                relief="flat",
                command=lambda nome=modulo: self.abrir_modulo(nome),
            ).pack(fill="x", padx=12, pady=4)

        self.content = ttk.Frame(self.root)
        self.content.pack(side="left", fill="both", expand=True)
        self.abrir_dashboard()

    def abrir_dashboard(self) -> None:
        self._limpar_content()
        frame = ttk.Frame(self.content, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="ERP CRM Autopecas & Servicos", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text=f"Usuario logado: {self.usuario.nome} | Perfil: {self.usuario.perfil.nome}",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(8, 20))
        ttk.Label(
            frame,
            text="Fases 2 a 4: cadastros basicos, estoque e compras.",
            font=("Segoe UI", 11),
        ).pack(anchor="w")

    def abrir_modulo(self, nome: str) -> None:
        self._limpar_content()
        if nome == "Dashboard":
            self.abrir_dashboard()
            return
        if nome in CADASTRO_MODULES:
            config = CADASTRO_MODULES[nome]
            CrudFrame(
                self.content,
                nome,
                config["controller"](),
                config["fields"],
                config["columns"],
            ).pack(fill="both", expand=True)
            return
        if nome == "Estoque":
            EstoqueFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        if nome == "Compras":
            CompraFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        if nome == "Vendas":
            VendaFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        frame = ttk.Frame(self.content, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=nome, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Modulo previsto para fase futura ou complemento da Fase 1.").pack(anchor="w", pady=(8, 0))

    def _limpar_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def run(self) -> None:
        self.root.mainloop()
