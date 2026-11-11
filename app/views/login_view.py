import tkinter as tk
from tkinter import messagebox

from app.config.settings import APP_NAME
from app.controllers.auth_controller import AuthController
from app.views.main_window import MainWindow


class TrocaSenhaDialog:
    """Janela modal de troca de senha obrigatoria (primeiro acesso ou senha redefinida)."""

    def __init__(self, parent: tk.Tk, controller: AuthController, usuario) -> None:
        self.controller = controller
        self.usuario = usuario
        self.concluido = False
        self.janela = tk.Toplevel(parent)
        self.janela.title("Troca de senha obrigatoria")
        self.janela.geometry("380x330")
        self.janela.resizable(False, False)
        self.janela.transient(parent)
        self.janela.grab_set()
        self.janela.protocol("WM_DELETE_WINDOW", self.janela.destroy)

        frame = tk.Frame(self.janela, padx=24, pady=18)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Defina uma nova senha", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(
            frame,
            text="Minimo de 8 caracteres, com letras e numeros.\nVoce precisa trocar a senha para continuar.",
            justify="left", fg="#667085",
        ).pack(anchor="w", pady=(2, 12))
        self.atual = self._campo(frame, "Senha atual")
        self.nova = self._campo(frame, "Nova senha")
        self.confirmacao = self._campo(frame, "Confirmar nova senha")
        tk.Button(frame, text="Salvar nova senha", command=self._salvar).pack(fill="x", pady=(14, 0))
        self.janela.bind("<Return>", lambda _e: self._salvar())
        self.atual.focus_set()

    @staticmethod
    def _campo(frame, rotulo: str) -> tk.Entry:
        tk.Label(frame, text=rotulo).pack(anchor="w")
        entry = tk.Entry(frame, show="*")
        entry.pack(fill="x", pady=(0, 6))
        return entry

    def _salvar(self) -> None:
        if self.nova.get() != self.confirmacao.get():
            messagebox.showerror("Troca de senha", "A confirmacao nao confere com a nova senha.", parent=self.janela)
            return
        try:
            self.controller.trocar_senha(self.usuario.id, self.atual.get(), self.nova.get())
        except ValueError as exc:
            messagebox.showerror("Troca de senha", str(exc), parent=self.janela)
            return
        self.concluido = True
        self.janela.destroy()

    def exibir(self) -> bool:
        self.janela.wait_window()
        return self.concluido


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
        try:
            usuario = self.controller.autenticar(self.login_entry.get(), self.senha_entry.get())
        except ValueError as exc:  # conta bloqueada por tentativas
            messagebox.showerror("Login", str(exc))
            return
        if usuario is None:
            messagebox.showerror("Login", "Usuario ou senha invalidos.")
            self.senha_entry.delete(0, "end")
            return

        if usuario.precisa_trocar_senha and not TrocaSenhaDialog(self.root, self.controller, usuario).exibir():
            self.controller.encerrar_sessao()
            self.senha_entry.delete(0, "end")
            return

        self.root.destroy()
        MainWindow(usuario).run()
