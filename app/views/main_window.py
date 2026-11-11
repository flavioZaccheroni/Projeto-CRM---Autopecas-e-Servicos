import tkinter as tk
from tkinter import ttk

from app.config.settings import APP_NAME
from app.controllers.auth_controller import AuthController
from app.utils.sessao import MENU_PARA_MODULO, Sessao
from app.views.admin_views import ConfiguracoesFrame, PermissoesFrame, UsuariosFrame
from app.views.compra_view import CompraFrame
from app.views.crud_view import CrudFrame
from app.views.estoque_view import EstoqueFrame
from app.views.financeiro_view import FinanceiroFrame
from app.views.module_configs import CADASTRO_MODULES
from app.views.os_view import OrdemServicoFrame
from app.views.relatorio_view import RelatorioFrame
from app.views.seguranca_view import SegurancaFrame
from app.views.theme import COLORS, configure_style
from app.views.venda_view import VendaFrame


class MainWindow:
    def __init__(self, usuario) -> None:
        self.usuario = usuario
        self.active_button: tk.Button | None = None
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1280x760")
        self.root.minsize(1100, 680)
        configure_style(self.root)

        sidebar = tk.Frame(self.root, width=240, bg=COLORS["sidebar"])
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="ERP Autopecas",
            fg="white",
            bg=COLORS["sidebar"],
            font=("Segoe UI", 15, "bold"),
            pady=18,
        ).pack(fill="x")
        tk.Label(
            sidebar,
            text="Operacao integrada",
            fg=COLORS["sidebar_muted"],
            bg=COLORS["sidebar"],
            font=("Segoe UI", 9),
        ).pack(fill="x", pady=(0, 14))

        menu_groups = [
            ("Principal", ["Dashboard"]),
            ("Cadastros", ["Clientes", "Veiculos", "Fornecedores", "Categorias", "Marcas", "Produtos"]),
            ("Operacao", ["Estoque", "Compras", "Vendas", "Ordem de Servico", "Financeiro", "Relatorios"]),
            ("Sistema", ["Seguranca e Backup", "Usuarios", "Permissoes", "Configuracoes"]),
        ]
        self.menu_buttons: dict[str, tk.Button] = {}
        for group_name, items in menu_groups:
            items = [m for m in items if self._pode_ver(m)]
            if not items:
                continue
            tk.Label(
                sidebar,
                text=group_name.upper(),
                fg=COLORS["sidebar_muted"],
                bg=COLORS["sidebar"],
                font=("Segoe UI", 8, "bold"),
                anchor="w",
            ).pack(fill="x", padx=18, pady=(12, 5))
            for modulo in items:
                button = tk.Button(
                    sidebar,
                    text=modulo,
                    anchor="w",
                    relief="flat",
                    bd=0,
                    padx=14,
                    pady=9,
                    fg=COLORS["sidebar_text"],
                    bg=COLORS["sidebar"],
                    activeforeground="#ffffff",
                    activebackground=COLORS["sidebar_hover"],
                    font=("Segoe UI", 10),
                    command=lambda nome=modulo: self.abrir_modulo(nome),
                )
                button.pack(fill="x", padx=12, pady=2)
                self.menu_buttons[modulo] = button

        tk.Button(
            sidebar,
            text=f"Sair ({self.usuario.login})",
            anchor="w",
            relief="flat",
            bd=0,
            padx=14,
            pady=9,
            fg=COLORS["sidebar_muted"],
            bg=COLORS["sidebar"],
            activeforeground="#ffffff",
            activebackground=COLORS["sidebar_hover"],
            font=("Segoe UI", 10),
            command=self.sair,
        ).pack(side="bottom", fill="x", padx=12, pady=12)

        self.content = ttk.Frame(self.root, style="App.TFrame")
        self.content.pack(side="left", fill="both", expand=True)
        self.abrir_dashboard()

    def abrir_dashboard(self) -> None:
        self._limpar_content()
        self._ativar_menu("Dashboard")
        frame = ttk.Frame(self.content, padding=26, style="Surface.TFrame")
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="ERP CRM Autopecas & Servicos", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            frame,
            text=f"Usuario logado: {self.usuario.nome} | Perfil: {self.usuario.perfil.nome}",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(6, 24))

        cards = ttk.Frame(frame, style="Surface.TFrame")
        cards.pack(fill="x", pady=(0, 18))
        for index, (title, value, detail) in enumerate(
            [
                ("Usuario", self.usuario.login, self.usuario.nome),
                ("Perfil", self.usuario.perfil.nome, "Define os modulos e acoes liberados no menu"),
                ("Modulos liberados", str(sum(1 for m in MENU_PARA_MODULO if m != "Dashboard" and self._pode_ver(m))), "Itens visiveis no menu lateral"),
            ]
        ):
            card = ttk.LabelFrame(cards, text=title, padding=16, style="Section.TLabelframe")
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 12))
            ttk.Label(card, text=value, font=("Segoe UI", 20, "bold")).pack(anchor="w")
            ttk.Label(card, text=detail, style="Subtle.TLabel", wraplength=260).pack(anchor="w", pady=(6, 0))
            cards.columnconfigure(index, weight=1)

        workflow = ttk.LabelFrame(frame, text="Fluxo operacional atual", padding=16, style="Section.TLabelframe")
        workflow.pack(fill="x")
        ttk.Label(
            workflow,
            text="Cadastre clientes e produtos, alimente o estoque por compras ou ajuste, finalize vendas para baixar saldo e gerar contas a receber.",
            style="Subtle.TLabel",
            wraplength=820,
        ).pack(anchor="w")

    def abrir_modulo(self, nome: str) -> None:
        self._limpar_content()
        self._ativar_menu(nome)
        if nome == "Dashboard":
            self.abrir_dashboard()
            return
        if not self._pode_ver(nome):
            ttk.Label(self.content, text="Acesso negado a este modulo.", padding=24).pack(anchor="w")
            return
        if nome == "Usuarios":
            UsuariosFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        if nome == "Permissoes":
            PermissoesFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        if nome == "Configuracoes":
            ConfiguracoesFrame(self.content, self.usuario).pack(fill="both", expand=True)
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
        if nome == "Ordem de Servico":
            OrdemServicoFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        if nome == "Financeiro":
            FinanceiroFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        if nome == "Relatorios":
            RelatorioFrame(self.content).pack(fill="both", expand=True)
            return
        if nome == "Seguranca e Backup":
            SegurancaFrame(self.content, self.usuario).pack(fill="both", expand=True)
            return
        frame = ttk.Frame(self.content, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=nome, font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Modulo previsto para fase futura ou complemento da Fase 1.").pack(anchor="w", pady=(8, 0))

    @staticmethod
    def _pode_ver(nome_menu: str) -> bool:
        modulo = MENU_PARA_MODULO.get(nome_menu)
        return modulo is None or Sessao.pode(modulo, "ver")

    def sair(self) -> None:
        AuthController().encerrar_sessao()
        self.root.destroy()
        from app.views.login_view import LoginView  # import tardio: login_view importa esta janela

        LoginView().run()

    def _limpar_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _ativar_menu(self, nome: str) -> None:
        if self.active_button:
            self.active_button.configure(bg=COLORS["sidebar"], fg=COLORS["sidebar_text"])
        button = self.menu_buttons.get(nome)
        if button:
            button.configure(bg=COLORS["sidebar_active"], fg="#ffffff")
            self.active_button = button

    def run(self) -> None:
        self.root.mainloop()
