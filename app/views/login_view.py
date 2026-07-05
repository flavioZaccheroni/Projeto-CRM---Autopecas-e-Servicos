import tkinter as tk
from tkinter import messagebox

from app.config.settings import APP_NAME
from app.controllers.auth_controller import AuthController
from app.views.main_window import MainWindow


class LoginView:
    def __init__(self) -> None:
        self.controller = AuthController()
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Login")
        self.root.geometry("360x220")
        self.root.resizable(False, False)

        frame = tk.Frame(self.root, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=APP_NAME, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 16))

        tk.Label(frame, text="Usuario").pack(anchor="w")
        self.login_entry = tk.Entry(frame)
        self.login_entry.pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Senha").pack(anchor="w")
        self.senha_entry = tk.Entry(frame, show="*")
        self.senha_entry.pack(fill="x", pady=(0, 16))

        tk.Button(frame, text="Entrar", command=self._entrar).pack(fill="x")
        self.root.bind("<Return>", lambda _event: self._entrar())

    def run(self) -> None:
        self.login_entry.focus_set()
        self.root.mainloop()

    def _entrar(self) -> None:
        usuario = self.controller.autenticar(self.login_entry.get(), self.senha_entry.get())
        if usuario is None:
            messagebox.showerror("Login", "Usuario ou senha invalidos.")
            return

        self.root.destroy()
        MainWindow(usuario).run()
