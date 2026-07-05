import tkinter as tk

from app.config.settings import APP_NAME


class MainWindow:
    def __init__(self, usuario) -> None:
        self.usuario = usuario
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("900x560")

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

        for modulo in ["Dashboard", "Usuarios", "Permissoes", "Configuracoes"]:
            tk.Button(sidebar, text=modulo, anchor="w", relief="flat").pack(fill="x", padx=12, pady=4)

        content = tk.Frame(self.root, padx=24, pady=24)
        content.pack(side="left", fill="both", expand=True)

        tk.Label(content, text="Base do sistema", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(
            content,
            text=f"Usuario logado: {usuario.nome} | Perfil: {usuario.perfil.nome}",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(8, 20))
        tk.Label(
            content,
            text="Fase 1 iniciada: login, banco, usuarios, perfis e permissoes.",
            font=("Segoe UI", 11),
        ).pack(anchor="w")

    def run(self) -> None:
        self.root.mainloop()
